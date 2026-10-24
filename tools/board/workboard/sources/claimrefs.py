"""Claim-ref source: one fetch of every live claim ref, read their claim.json payloads (authoritative owners)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from .. import claims, gitutil
from ..model import FetchResult, Finding, Observation, SourceHealth

NAME = "claims"


class ClaimRefSource:
    name = NAME

    def __init__(self, cfg, *, state_dir=None):
        self.cfg, self.state_dir = cfg, state_dir

    def fetch(self, *, since=None, timeout_seconds=20) -> FetchResult:
        now = datetime.now(timezone.utc)
        if not self.cfg.ledger.remote:
            return FetchResult([], SourceHealth(NAME, False, None, 0, "no ledger remote"), [])
        repo = claims._repo(self.state_dir)
        pr = claims.ensure_probe(self.cfg, self.state_dir)
        if not pr.ok:
            return FetchResult([], SourceHealth(NAME, False, now, 0, f"claims disabled: {pr.detail}"),
                               [Finding("SYNC_FAILED", "warn", "claim refs disabled (probe failed)",
                                        "workboard status; claims shown from the ledger are advisory")])
        prefix = pr.prefix
        p = claims._git(repo, "fetch", "-q", "--prune", self.cfg.ledger.remote, f"+{prefix}/*:refs/live-claims/*",
                        timeout=timeout_seconds)
        if p.returncode != 0:
            why = gitutil.err(p)
            return FetchResult([], SourceHealth(NAME, False, now, 0, why),
                               [Finding("SYNC_FAILED", "warn", f"claim refs unreadable: {why}",
                                        "claims shown from the ledger are advisory until this works")])
        listing = claims._git(repo, "for-each-ref", "--format=%(objectname) %(refname)", "refs/live-claims/")
        obs = []
        refs = [l.split(" ", 1) for l in listing.stdout.splitlines() if l.strip()]
        if len(refs) > self.cfg.claims.max_live_claims:
            refs = refs[: self.cfg.claims.max_live_claims]
        for oid, _ref in refs:
            out = claims._git(repo, "show", f"{oid}:claim.json")
            try:
                payload = json.loads(out.stdout) if out.returncode == 0 else None
            except ValueError:
                payload = None
            if not isinstance(payload, dict) or not isinstance(payload.get("entity_id"), str):
                continue
            fields = {"claims.oid": oid, "claims.session_id": payload.get("session_id", ""),
                      "claims.alias": payload.get("alias", ""), "claims.host": payload.get("host", ""),
                      "claims.renewed_at": payload.get("renewed_at"), "claims.acquired_at": payload.get("acquired_at")}
            obs.append(Observation(NAME, payload["entity_id"], now, fields, {k: "authoritative" for k in fields}))
        return FetchResult(obs, SourceHealth(NAME, True, now, 120, f"{len(obs)} live claim(s)"), [])
