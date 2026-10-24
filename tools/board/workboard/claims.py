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


class Disabled(Exception):
    """Claims are off until a probe has passed for the configured remote."""


def _fingerprint(remote: str) -> str:
    return hashlib.sha256(remote.encode("utf-8")).hexdigest()[:16]


def probed_prefix(cfg, state_dir) -> str | None:
    try:
        rec = json.loads((_state(state_dir) / PROBE_FILE).read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(rec, dict) or rec.get("remote") != _fingerprint(cfg.ledger.remote):
        return None
    return rec.get("prefix") if rec.get("prefix") in (DEFAULT_PREFIX, FALLBACK_PREFIX) else None


def _prefix(state_dir, cfg=None) -> str:
    """Probed namespace for cfg's remote; raises Disabled when no probe has passed for it."""
    if cfg is None:
        raise Disabled("no config")
    pre = probed_prefix(cfg, state_dir)
    if not pre:
        raise Disabled("claims are disabled until `workboard status --probe` passes for this ledger remote")
    return pre


def ensure_probe(cfg, state_dir) -> "ProbeResult":
    pre = probed_prefix(cfg, state_dir)
    return ProbeResult(True, pre, "cached") if pre else probe(cfg, state_dir=state_dir)


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
    except OSError as exc:
        return subprocess.CompletedProcess(args, 127, "", str(exc))


def _commit(repo, payload: dict, parent: str | None) -> str:
    b = _git(repo, "hash-object", "-w", "--stdin", input_text=json.dumps(payload, sort_keys=True))
    if b.returncode != 0:
        raise RuntimeError(f"hash-object failed: {gitutil.err(b)}")
    t = _git(repo, "mktree", input_text=f"100644 blob {b.stdout.strip()}\tclaim.json\n")
    if t.returncode != 0:
        raise RuntimeError(f"mktree failed: {gitutil.err(t)}")
    tree = t.stdout.strip()
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
    """Create/read/renew/delete a throwaway claim ref, verifying each step by reading the remote; record which
    namespace works for this exact remote. A partial success cleans up its temporary ref."""
    repo = _repo(state_dir)
    actor = {"session_id": "probe", "alias": "probe"}
    errors = []
    for prefix in (DEFAULT_PREFIX, FALLBACK_PREFIX):
        ref = f"{prefix}/probe-{uuid.uuid4().hex[:12]}"
        tip = None
        try:
            oid = _commit(repo, _new_payload("probe", actor, _now()), None)
            if _push(cfg, repo, [f"{oid}:{ref}"], TIMEOUT).returncode != 0 or _remote_oid(cfg, repo, ref) != oid:
                raise RuntimeError("create/read failed")
            tip = oid
            oid2 = _commit(repo, _new_payload("probe", actor, _now()), oid)
            if (_push(cfg, repo, [f"--force-with-lease={ref}:{oid}", f"{oid2}:{ref}"], TIMEOUT).returncode != 0
                    or _remote_oid(cfg, repo, ref) != oid2):
                raise RuntimeError("renew failed")
            tip = oid2
            if (_push(cfg, repo, [f"--force-with-lease={ref}:{oid2}", f":{ref}"], TIMEOUT).returncode != 0
                    or _remote_oid(cfg, repo, ref) is not None):
                raise RuntimeError("delete failed")
            tip = None
        except (RuntimeError, Offline) as exc:
            errors.append(f"{prefix}: {exc}")
            if tip:
                _push(cfg, repo, [f"--force-with-lease={ref}:{tip}", f":{ref}"], TIMEOUT)
            continue
        rec = {"prefix": prefix, "remote": _fingerprint(cfg.ledger.remote), "at": _now().isoformat()}
        (_state(state_dir) / PROBE_FILE).write_text(json.dumps(rec))
        return ProbeResult(True, prefix, "ok")
    try:
        (_state(state_dir) / PROBE_FILE).unlink()
    except OSError:
        pass
    return ProbeResult(False, "", "; ".join(errors))


def _valid_payload(p: dict, entity_id: str) -> bool:
    return (isinstance(p, dict) and p.get("entity_id") == entity_id and isinstance(p.get("session_id"), str)
            and p["session_id"] and _aware(p.get("renewed_at")) is not None)


def _aware(value):
    try:
        t = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return t if t.tzinfo else None


def _live_count(cfg, repo, prefix) -> int:
    p = _git(repo, "ls-remote", cfg.ledger.remote, f"{prefix}/*")
    if p.returncode != 0:
        raise Offline(gitutil.err(p))
    return sum(1 for l in p.stdout.splitlines() if l.strip() and "/probe-" not in l)


def _ctx(cfg, entity_id, state_dir):
    return _repo(state_dir), ref_for(entity_id, _prefix(state_dir, cfg))


def read(cfg, entity_id, *, state_dir=None) -> ClaimResult:
    try:
        repo, ref = _ctx(cfg, entity_id, state_dir)
    except Disabled as exc:
        return ClaimResult("REFUSED", None, str(exc))
    try:
        oid = _remote_oid(cfg, repo, ref)
    except Offline as exc:
        return ClaimResult("PENDING", None, f"remote unreachable: {exc}")
    if not oid:
        return ClaimResult("FREE")
    return ClaimResult("HELD", oid, "", _payload(cfg, repo, ref, oid))


def acquire(cfg, entity_id, actor, *, state_dir=None, now=None) -> ClaimResult:
    try:
        repo, ref = _ctx(cfg, entity_id, state_dir)
        if _live_count(cfg, repo, ref.rsplit("/", 1)[0]) >= cfg.claims.max_live_claims:
            return ClaimResult("REFUSED", None, f"live-claim limit ({cfg.claims.max_live_claims}) reached")
        oid = _commit(repo, _new_payload(entity_id, actor, now or _now()), None)
    except Disabled as exc:
        return ClaimResult("REFUSED", None, str(exc))
    except Offline as exc:
        return ClaimResult("PENDING", None, f"remote unreachable: {exc}")
    except RuntimeError as exc:
        return ClaimResult("REFUSED", None, str(exc))
    p = _push(cfg, repo, [f"{oid}:{ref}"], TIMEOUT)
    if p.returncode == 0:
        return ClaimResult("ACQUIRED", oid, "created", _payload(cfg, repo, ref, oid))
    return _resolve(cfg, repo, ref, oid, gitutil.err(p))


def _owned(cfg, repo, ref, entity_id, actor, expected_oid):
    """Payload at expected_oid if it is a complete claim for entity_id owned by actor; else a refusal."""
    base = _payload(cfg, repo, ref, expected_oid)
    if not _valid_payload(base, entity_id):
        return None, ClaimResult("REFUSED", expected_oid, "claim payload missing, malformed or for another task", base)
    if base["session_id"] != actor.get("session_id"):
        return None, ClaimResult("REFUSED", expected_oid, f"owned by {base.get('alias')}", base)
    return base, None


def heartbeat(cfg, entity_id, actor, *, expected_oid, state_dir=None, now=None) -> ClaimResult:
    try:
        repo, ref = _ctx(cfg, entity_id, state_dir)
    except Disabled as exc:
        return ClaimResult("REFUSED", None, str(exc))
    base, refusal = _owned(cfg, repo, ref, entity_id, actor, expected_oid)
    if refusal:
        return refusal
    try:
        oid = _commit(repo, _new_payload(entity_id, actor, now or _now(), base), expected_oid)
    except RuntimeError as exc:
        return ClaimResult("REFUSED", expected_oid, str(exc))
    p = _push(cfg, repo, [f"--force-with-lease={ref}:{expected_oid}", f"{oid}:{ref}"], TIMEOUT)
    if p.returncode == 0:
        return ClaimResult("ACQUIRED", oid, "renewed", _payload(cfg, repo, ref, oid))
    return _resolve(cfg, repo, ref, oid, gitutil.err(p))


def release(cfg, entity_id, actor, *, expected_oid, state_dir=None) -> ClaimResult:
    try:
        repo, ref = _ctx(cfg, entity_id, state_dir)
    except Disabled as exc:
        return ClaimResult("REFUSED", None, str(exc))
    _, refusal = _owned(cfg, repo, ref, entity_id, actor, expected_oid)
    if refusal:
        return refusal
    p = _push(cfg, repo, [f"--force-with-lease={ref}:{expected_oid}", f":{ref}"], TIMEOUT)
    if p.returncode == 0:
        return ClaimResult("RELEASED", None, "deleted")
    try:
        now_oid = _remote_oid(cfg, repo, ref)
    except Offline as exc:
        return ClaimResult("PENDING", expected_oid, f"remote unreachable: {exc}")
    if now_oid is None:
        return ClaimResult("RELEASED", None, "already gone")
    return ClaimResult("REFUSED", now_oid, "claim tip changed (someone renewed or stole it)",
                       _payload(cfg, repo, ref, now_oid))


def boot_id() -> str:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        return "unknown"


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


def steal(cfg, entity_id, actor, *, source_healthy: bool, clock_healthy: bool, state_dir=None, now=None,
          monotonic=None, boot=None) -> ClaimResult:
    """Take an expired claim, only with healthy claim source + clock evidence, after its tip stayed unchanged
    for >= 2 heartbeat intervals on this boot's monotonic clock."""
    if not (source_healthy and clock_healthy):
        return ClaimResult("REFUSED", None, "steal needs a healthy claim source and clock")
    now = now or _now()
    mono = time.monotonic() if monotonic is None else monotonic
    boot = boot or boot_id()
    try:
        repo, ref = _ctx(cfg, entity_id, state_dir)
        tip = _remote_oid(cfg, repo, ref)
    except Disabled as exc:
        return ClaimResult("REFUSED", None, str(exc))
    except Offline as exc:
        return ClaimResult("PENDING", None, f"remote unreachable: {exc}")
    if tip is None:
        return acquire(cfg, entity_id, actor, state_dir=state_dir, now=now)
    base = _payload(cfg, repo, ref, tip)
    if not _valid_payload(base, entity_id):
        return ClaimResult("REFUSED", tip, "claim payload missing or malformed; not stealing", base)
    renewed = _aware(base["renewed_at"])
    if renewed - now > timedelta(seconds=cfg.claims.clock_skew_warn_seconds):
        return ClaimResult("REFUSED", tip, "claim is dated in the future (clock skew); not stealing", base)
    if now - renewed <= timedelta(hours=cfg.claims.expire_after_hours):
        return ClaimResult("REFUSED", tip, "claim is not expired", base)
    grace = _grace(state_dir)
    need = 2 * cfg.claims.heartbeat_interval_minutes * 60
    seen = grace.get(ref)
    if not (isinstance(seen, list) and len(seen) == 3 and seen[0] == tip and seen[2] == boot and mono >= seen[1]):
        grace[ref] = [tip, mono, boot]
        _save_grace(state_dir, grace)
        return ClaimResult("REFUSED", tip, f"expired; grace period started ({need // 60} min unchanged before steal)", base)
    if mono - seen[1] < need:
        return ClaimResult("REFUSED", tip, f"grace period: {int(need - (mono - seen[1]))}s left", base)
    try:
        oid = _commit(repo, _new_payload(entity_id, actor, now, {"stolen_from": base.get("alias", "")}), tip)
    except RuntimeError as exc:
        return ClaimResult("REFUSED", tip, str(exc))
    p = _push(cfg, repo, [f"--force-with-lease={ref}:{tip}", f"{oid}:{ref}"], TIMEOUT)
    grace.pop(ref, None)
    _save_grace(state_dir, grace)
    if p.returncode == 0:
        return ClaimResult("ACQUIRED", oid, "stolen after expiry", _payload(cfg, repo, ref, oid))
    return _resolve(cfg, repo, ref, oid, gitutil.err(p))
