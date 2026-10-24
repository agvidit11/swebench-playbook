"""Claim-ref source: every live claim ref and its claim.json payload (authoritative owners).

A snapshot is healthy only if it is complete and valid: any malformed payload, a payload whose task does not
hash to its ref, a future-dated renewal, or more refs than max_live_claims makes it unhealthy, so the
projection falls back to explicitly advisory ledger data instead of showing omitted tasks as FREE.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .. import claims
from ..model import FetchResult, Finding, Observation, SourceHealth

NAME = "claims"


def _aware(value):
    try:
        t = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return t if t.tzinfo else None


class ClaimRefSource:
    name = NAME

    def __init__(self, cfg, *, state_dir=None, store=None):
        self.cfg, self.state_dir = cfg, state_dir
        self.store = store or claims.ClaimStore(cfg, state_dir)

    def _bad(self, now, why):
        return FetchResult([], SourceHealth(NAME, False, now, 0, why),
                           [Finding("SYNC_FAILED", "warn", f"claim refs unusable: {why}",
                                    "owners below come from the ledger and are advisory until fixed")])

    def fetch(self, *, since=None, timeout_seconds=20) -> FetchResult:
        now = datetime.now(timezone.utc)
        if not self.cfg.ledger.remote:
            return FetchResult([], SourceHealth(NAME, False, None, 0, "no ledger remote"), [])
        ok, detail, rows = self.store.snapshot(timeout=timeout_seconds)
        if not ok:
            return self._bad(now, detail)
        if len(rows) > self.cfg.claims.max_live_claims:
            return self._bad(now, f"{len(rows)} live claims exceed max_live_claims={self.cfg.claims.max_live_claims}")
        skew = timedelta(seconds=self.cfg.claims.clock_skew_warn_seconds)
        obs = []
        for ref, oid, payload in rows:
            ent = payload.get("entity_id") if isinstance(payload, dict) else None
            renewed = _aware(payload.get("renewed_at")) if isinstance(payload, dict) else None
            if not (isinstance(ent, str) and ent and isinstance(payload.get("session_id"), str) and payload["session_id"]
                    and renewed and claims.ref_for(ent, ref.rsplit("/", 1)[0]) == ref):
                return self._bad(now, f"malformed claim at {ref}")
            if renewed - now > skew:
                return self._bad(now, f"claim at {ref} is dated in the future (clock skew)")
            fields = {"claims.oid": oid, "claims.session_id": payload["session_id"],
                      "claims.alias": payload.get("alias", ""), "claims.host": payload.get("host", ""),
                      "claims.kind": payload.get("kind", ""), "claims.person": payload.get("person", ""),
                      "claims.renewed_at": payload["renewed_at"], "claims.acquired_at": payload.get("acquired_at")}
            obs.append(Observation(NAME, ent, now, fields, {k: "authoritative" for k in fields}))
        return FetchResult(obs, SourceHealth(NAME, True, now, 120, f"{len(obs)} live claim(s)"), [])
