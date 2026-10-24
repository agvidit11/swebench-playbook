"""Claims: atomic online acquisition through create-only git refs on the ledger remote (DESIGN §5).

A claim is a ref `refs/claims/<sha256(task)[:16]>` pointing at a tiny commit holding claim.json. Creating the
ref is a plain (non-forced) push, so of two concurrent creates exactly one wins. Renew, steal and release
use --force-with-lease=<ref>:<observed oid>, so they only succeed against the exact tip they observed.
Only the push result or a fresh read of the remote ref counts; local state never claims success.
Objects are built in a private bare repo under the state dir, so the user's checkouts are never touched.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import gitutil
from .sync import default_state_dir

PROBE_FILE = "claims-probe.json"
GRACE_FILE = "steal-grace.json"
OBJECTS = "claims-objects.git"
DEFAULT_PREFIX = "refs/claims"
FALLBACK_PREFIX = "refs/heads/workboard-claims"
TIMEOUT = 20
GIT_ID = {"GIT_AUTHOR_NAME": "workboard", "GIT_AUTHOR_EMAIL": "workboard@localhost",
          "GIT_COMMITTER_NAME": "workboard", "GIT_COMMITTER_EMAIL": "workboard@localhost"}


class Offline(Exception):
    pass


@dataclass
class ClaimResult:
    status: str                     # ACQUIRED | LOST | RETRY | RELEASED | REFUSED | PENDING | HELD | FREE
    oid: str | None = None
    detail: str = ""
    owner: dict = field(default_factory=dict)


@dataclass
class ProbeResult:
    ok: bool
    prefix: str
    detail: str = ""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _state(state_dir) -> Path:
    d = Path(state_dir or default_state_dir())
    d.mkdir(parents=True, exist_ok=True)
    return d


def _prefix(state_dir) -> str:
    try:
        return json.loads((_state(state_dir) / PROBE_FILE).read_text()).get("prefix", DEFAULT_PREFIX)
    except (OSError, ValueError):
        return DEFAULT_PREFIX


def ref_for(entity_id: str, prefix: str = DEFAULT_PREFIX) -> str:
    return f"{prefix}/{hashlib.sha256(entity_id.encode('utf-8')).hexdigest()[:16]}"


def _repo(state_dir) -> Path:
    repo = _state(state_dir) / OBJECTS
    if not (repo / "HEAD").exists():
        gitutil.run(repo.parent, "init", "-q", "--bare", str(repo))
    return repo


def _git(repo, *args, input_text=None, timeout=TIMEOUT):
    import subprocess
    try:
        return subprocess.run(["git", *args], cwd=repo, input=input_text, capture_output=True, text=True,
                              timeout=timeout, env={**gitutil.ENV, **GIT_ID})
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, 124, "", "timeout")


def _commit(repo, payload: dict, parent: str | None) -> str:
    blob = _git(repo, "hash-object", "-w", "--stdin", input_text=json.dumps(payload, sort_keys=True)).stdout.strip()
    tree = _git(repo, "mktree", input_text=f"100644 blob {blob}\tclaim.json\n").stdout.strip()
    args = ["commit-tree", tree, "-m", f"claim {payload['entity_id']} by {payload.get('alias', '')}"]
    if parent:
        args[2:2] = ["-p", parent]
    out = _git(repo, *args)
    if out.returncode != 0:
        raise RuntimeError(f"commit-tree failed: {gitutil.err(out)}")
    return out.stdout.strip()


def _push(cfg, repo, args, timeout):
    return _git(repo, "push", "--porcelain", cfg.ledger.remote, *args, timeout=timeout)


def _remote_oid(cfg, repo, ref) -> str | None:
    p = _git(repo, "ls-remote", cfg.ledger.remote, ref)
    if p.returncode != 0:
        raise Offline(gitutil.err(p))
    for line in p.stdout.splitlines():
        oid, name = line.split("\t", 1)
        if name == ref:
            return oid
    return None


def _payload(cfg, repo, ref, oid) -> dict:
    if _git(repo, "cat-file", "-e", oid).returncode != 0:
        _git(repo, "fetch", "-q", cfg.ledger.remote, f"+{ref}:refs/seen/{oid[:16]}")
    p = _git(repo, "show", f"{oid}:claim.json")
    try:
        return json.loads(p.stdout) if p.returncode == 0 else {}
    except ValueError:
        return {}


def _new_payload(entity_id, actor, now, base: dict | None = None, **extra) -> dict:
    p = dict(base or {})
    p.update(entity_id=entity_id, nonce=str(uuid.uuid4()), renewed_at=now.isoformat(timespec="seconds"),
             session_id=actor.get("session_id", ""), alias=actor.get("alias", ""), host=actor.get("host", ""),
             kind=actor.get("kind", "claude"))
    p.setdefault("claim_id", str(uuid.uuid4()))
    p.setdefault("acquired_at", p["renewed_at"])
    p.update(extra)
    return p


def _resolve(cfg, repo, ref, mine: str, detail: str) -> ClaimResult:
    """After a failed/uncertain push: the remote ref decides."""
    try:
        now_oid = _remote_oid(cfg, repo, ref)
    except Offline as exc:
        return ClaimResult("PENDING", None, f"remote unreachable: {exc}")
    if now_oid == mine:
        return ClaimResult("ACQUIRED", mine, "push outcome was uncertain; remote shows our claim")
    if now_oid is None:
        return ClaimResult("RETRY", None, detail)
    return ClaimResult("LOST", now_oid, detail, _payload(cfg, repo, ref, now_oid))


# ------------------------------------------------------------------------------------------------- API
def probe(cfg, *, state_dir=None) -> ProbeResult:
    """Create/read/renew/delete a throwaway claim ref; remember which namespace works."""
    repo = _repo(state_dir)
    actor = {"session_id": "probe", "alias": "probe"}
    errors = []
    for prefix in (DEFAULT_PREFIX, FALLBACK_PREFIX):
        ref = f"{prefix}/probe-{uuid.uuid4().hex[:12]}"
        try:
            oid = _commit(repo, _new_payload("probe", actor, _now()), None)
            steps = [("create", [f"{oid}:{ref}"])]
            if _push(cfg, repo, steps[0][1], TIMEOUT).returncode != 0 or _remote_oid(cfg, repo, ref) != oid:
                raise RuntimeError("create/read failed")
            oid2 = _commit(repo, _new_payload("probe", actor, _now()), oid)
            if _push(cfg, repo, [f"--force-with-lease={ref}:{oid}", f"{oid2}:{ref}"], TIMEOUT).returncode != 0:
                raise RuntimeError("renew failed")
            if _push(cfg, repo, [f"--force-with-lease={ref}:{oid2}", f":{ref}"], TIMEOUT).returncode != 0:
                raise RuntimeError("delete failed")
        except (RuntimeError, Offline) as exc:
            errors.append(f"{prefix}: {exc}")
            continue
        (_state(state_dir) / PROBE_FILE).write_text(json.dumps({"prefix": prefix, "at": _now().isoformat()}))
        return ProbeResult(True, prefix, "ok")
    return ProbeResult(False, "", "; ".join(errors))


def read(cfg, entity_id, *, state_dir=None) -> ClaimResult:
    repo, ref = _repo(state_dir), ref_for(entity_id, _prefix(state_dir))
    try:
        oid = _remote_oid(cfg, repo, ref)
    except Offline as exc:
        return ClaimResult("PENDING", None, f"remote unreachable: {exc}")
    if not oid:
        return ClaimResult("FREE")
    return ClaimResult("HELD", oid, "", _payload(cfg, repo, ref, oid))


def acquire(cfg, entity_id, actor, *, state_dir=None, now=None) -> ClaimResult:
    repo, ref = _repo(state_dir), ref_for(entity_id, _prefix(state_dir))
    oid = _commit(repo, _new_payload(entity_id, actor, now or _now()), None)
    p = _push(cfg, repo, [f"{oid}:{ref}"], TIMEOUT)
    if p.returncode == 0:
        return ClaimResult("ACQUIRED", oid, "created", _payload(cfg, repo, ref, oid))
    return _resolve(cfg, repo, ref, oid, gitutil.err(p))


def heartbeat(cfg, entity_id, actor, observed_oid, *, state_dir=None, now=None) -> ClaimResult:
    repo, ref = _repo(state_dir), ref_for(entity_id, _prefix(state_dir))
    base = _payload(cfg, repo, ref, observed_oid)
    if base and base.get("session_id") != actor.get("session_id"):
        return ClaimResult("REFUSED", observed_oid, "not the owner", base)
    oid = _commit(repo, _new_payload(entity_id, actor, now or _now(), base), observed_oid)
    p = _push(cfg, repo, [f"--force-with-lease={ref}:{observed_oid}", f"{oid}:{ref}"], TIMEOUT)
    if p.returncode == 0:
        return ClaimResult("ACQUIRED", oid, "renewed", _payload(cfg, repo, ref, oid))
    return _resolve(cfg, repo, ref, oid, gitutil.err(p))


def release(cfg, entity_id, actor, observed_oid, *, state_dir=None) -> ClaimResult:
    repo, ref = _repo(state_dir), ref_for(entity_id, _prefix(state_dir))
    p = _push(cfg, repo, [f"--force-with-lease={ref}:{observed_oid}", f":{ref}"], TIMEOUT)
    if p.returncode == 0:
        return ClaimResult("RELEASED", None, "deleted")
    try:
        now_oid = _remote_oid(cfg, repo, ref)
    except Offline as exc:
        return ClaimResult("PENDING", observed_oid, f"remote unreachable: {exc}")
    if now_oid is None:
        return ClaimResult("RELEASED", None, "already gone")
    return ClaimResult("REFUSED", now_oid, "claim tip changed (someone renewed or stole it)",
                       _payload(cfg, repo, ref, now_oid))


def _grace(state_dir) -> dict:
    try:
        return json.loads((_state(state_dir) / GRACE_FILE).read_text())
    except (OSError, ValueError):
        return {}


def _save_grace(state_dir, data) -> None:
    d = _state(state_dir)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".grace-")
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh)
    os.replace(tmp, d / GRACE_FILE)


def steal(cfg, entity_id, actor, *, state_dir=None, now=None, monotonic=None) -> ClaimResult:
    """Take an expired claim: only after its tip stayed unchanged for >= 2 heartbeat intervals (monotonic)."""
    now = now or _now()
    mono = time.monotonic() if monotonic is None else monotonic
    repo, ref = _repo(state_dir), ref_for(entity_id, _prefix(state_dir))
    try:
        tip = _remote_oid(cfg, repo, ref)
    except Offline as exc:
        return ClaimResult("PENDING", None, f"remote unreachable: {exc}")
    if tip is None:
        return acquire(cfg, entity_id, actor, state_dir=state_dir, now=now)
    base = _payload(cfg, repo, ref, tip)
    renewed = datetime.fromisoformat(base.get("renewed_at", now.isoformat()))
    if now - renewed <= timedelta(hours=cfg.claims.expire_after_hours):
        return ClaimResult("REFUSED", tip, "claim is not expired", base)
    grace = _grace(state_dir)
    need = 2 * cfg.claims.heartbeat_interval_minutes * 60
    seen = grace.get(ref)
    if not seen or seen[0] != tip or mono < seen[1]:
        grace[ref] = [tip, mono]
        _save_grace(state_dir, grace)
        return ClaimResult("REFUSED", tip, f"expired; grace period started ({need // 60} min unchanged before steal)", base)
    if mono - seen[1] < need:
        return ClaimResult("REFUSED", tip, f"grace period: {int(need - (mono - seen[1]))}s left", base)
    oid = _commit(repo, _new_payload(entity_id, actor, now, {"stolen_from": base.get("alias", "")}), tip)
    p = _push(cfg, repo, [f"--force-with-lease={ref}:{tip}", f"{oid}:{ref}"], TIMEOUT)
    grace.pop(ref, None)
    _save_grace(state_dir, grace)
    if p.returncode == 0:
        return ClaimResult("ACQUIRED", oid, "stolen after expiry", _payload(cfg, repo, ref, oid))
    return _resolve(cfg, repo, ref, oid, gitutil.err(p))
