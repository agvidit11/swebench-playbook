import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from workboard.config import load_config
from workboard.model import Observation
from workboard import events
from workboard.projection import project, REPO_ENTITY_PREFIX

NOW = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)
SHA_A, SHA_B, SHA_S = "a" * 40, "b" * 40, "c" * 40


def cm(name, status="draft", valid="passing", **kw):
    f = {"codimango.status": status, "codimango.validation_status": valid, "codimango.created_at": "2026-10-20T00:00:00Z",
         "codimango.commit_sha": SHA_S, "codimango.validation_commit_sha": SHA_S, "codimango.reviewed_at": None,
         "codimango.entered_pool_at": None, "codimango.track": "swe-bench-multi-turn"}
    f.update({f"codimango.{k}": v for k, v in kw.items()})
    return Observation("codimango", name, NOW, f)


def gt(name, head=SHA_A, head_time="2026-10-21T00:00:00+00:00", times=None, changed=None):
    f = {"git.task_head": head, "git.task_head_time": head_time, "git.commit_times": times or [head_time], "git.repo": "tasks"}
    if changed is not None:
        f["git.changed_since_validated"] = changed
    return Observation("git", name, NOW, f)


def repo(times):
    return Observation("git", REPO_ENTITY_PREFIX + "tasks", NOW, {"git.commit_time_by_sha": times})


def e(type, task, payload=None, session="s1", alias="h1·tab", host="h1", seq=1, commit=None, at="2026-10-23T19:00:00+00:00"):
    ev = events.new_event(type, task, payload or {}, actor={"session_id": session, "alias": alias, "kind": "claude"},
                          commit=commit, source="test")
    ev = events.stamp(ev, host, seq)
    ev["occurred_at"] = at
    return ev


class ProjectionTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(Path("/nonexistent"))

    def view(self, obs, evs=(), name="t"):
        views = {v.entity_id: v for v in project(list(obs), list(evs), self.cfg, NOW)}
        return views[name]

    def test_used_in_training_counts_accepted(self):
        v = self.view([cm("t", "used_in_training", reviewed_at="2026-10-22T00:00:00Z")])
        self.assertEqual(v.fields["state"], "ACCEPTED")
        self.assertEqual(v.fields["group"], "DONE")

    def test_r2_needs_two_sessions_same_commit(self):
        obs = [cm("t"), gt("t"), repo({SHA_S: "2026-10-22T00:00:00+00:00"})]
        one = [e("review", "t", {"verdict": "ready", "confidence": 4}, commit=SHA_A)]
        self.assertEqual(self.view(obs, one).fields["review"], "R1")
        same_session_twice = one + [e("review", "t", {"verdict": "ready", "confidence": 5}, commit=SHA_A, seq=2)]
        self.assertEqual(self.view(obs, same_session_twice).fields["review"], "R1")
        two_indep = one + [e("review", "t", {"verdict": "ready", "confidence": 5}, session="s2", host="h2", commit=SHA_A)]
        self.assertEqual(self.view(obs, two_indep).fields["review"], "R1")     # two fresh agents, no author approval
        two = one + [e("review", "t", {"verdict": "ready", "confidence": 5, "role": "author"}, session="s2", host="h2", commit=SHA_A)]
        v = self.view(obs, two)
        self.assertEqual(v.fields["review"], "R2")
        self.assertEqual(v.fields["next"], "RUN check")        # presubmit is required before submit
        one = two + [e("check", "t", {"pass": 20, "warn": 1, "fail": 0}, commit=SHA_A)]
        self.assertEqual(self.view(obs, one).fields["next"], "RUN check")            # R2 + one presubmit is not enough
        checked = one + [e("check", "t", {"pass": 20, "warn": 0, "fail": 0, "role": "author"}, session="s3", commit=SHA_A)]
        self.assertEqual(self.view(obs, checked).fields["next"], "SUBMIT")
        same = one_session_both = [e("review", "t", {"verdict": "ready", "role": "author"}, commit=SHA_A, seq=5),
                                   e("review", "t", {"verdict": "ready", "role": "independent"}, commit=SHA_A, seq=6)]
        self.assertNotEqual(self.view(obs, same).fields["review"], "R2")           # one session cannot fill both slots

    def test_new_commit_makes_review_stale(self):
        obs = [cm("t"), gt("t", head=SHA_B), repo({SHA_S: "2026-10-22T00:00:00+00:00"})]
        evs = [e("review", "t", {"verdict": "ready", "confidence": 4}, commit=SHA_A)]
        v = self.view(obs, evs)
        self.assertEqual(v.fields["review"], "R~")
        self.assertTrue(v.fields["confidence_stale"])

    def test_changes_verdict_not_counted_and_visible(self):
        obs = [cm("t"), gt("t"), repo({SHA_S: "2026-10-22T00:00:00+00:00"})]
        evs = [e("review", "t", {"verdict": "ready", "confidence": 4, "role": "author"}, commit=SHA_A),
               e("review", "t", {"verdict": "changes", "confidence": 2}, session="s2", host="h2", commit=SHA_A)]
        v = self.view(obs, evs)
        self.assertEqual(v.fields["review"], "R1")                     # author ready; independent asked for changes
        self.assertEqual(v.fields["gates"]["independent"]["review"]["state"], "bad")
        self.assertEqual(v.fields["dissent"], 1)

    def test_required_keys_present(self):
        keys = {"state", "state_age_s", "owner", "claim_health", "review", "confidence", "check", "pushes", "round",
                "valid", "sync", "next", "group"}
        cm_view = self.view([cm("t")])
        git_only = self.view([gt("t")])
        self.assertTrue(keys <= set(cm_view.fields), keys - set(cm_view.fields))
        self.assertTrue(keys <= set(git_only.fields), keys - set(git_only.fields))

    def test_next_priority_order(self):
        base = [gt("t"), repo({SHA_S: "2026-10-22T00:00:00+00:00"})]
        conflict = [e("claim", "t", seq=1), e("claim", "t", session="s9", alias="h2·x", host="h2", seq=1)]
        # conflict beats failing validation
        self.assertEqual(self.view([cm("t", valid="failed")] + base, conflict).fields["next"], "RESOLVE CONFLICT")
        # failing validation beats drift
        drift = [cm("t", valid="failed", validation_commit_sha=SHA_B)] + base
        self.assertEqual(self.view(drift).fields["next"], "FIX validation")
        # stale validation on a passing draft blocks the ladder
        v = self.view([cm("t", validation_commit_sha=SHA_B)] + base,
                      [e("check", "t", {"pass": 1}, commit=SHA_A),
                       e("review", "t", {"verdict": "ready"}, commit=SHA_A),
                       e("review", "t", {"verdict": "ready", "role": "author"}, session="s2", host="h2", commit=SHA_A)])
        self.assertEqual((v.fields["group"], v.fields["next"]), ("ATTENTION", "RERUN server"))
        # full ladder
        ladder = [([], "RUN check"),
                  ([e("check", "t", {"pass": 1}, commit=SHA_A)], "RUN check"),
                  ([e("check", "t", {"pass": 1}, commit=SHA_A), e("check", "t", {"pass": 1, "role": "author"}, session="s3", commit=SHA_A)], "GET R1"),
                  ([e("check", "t", {"pass": 1}, commit=SHA_A), e("check", "t", {"pass": 1, "role": "author"}, session="s3", commit=SHA_A), e("review", "t", {"verdict": "ready"}, commit=SHA_A)], "GET R2"),
                  ([e("check", "t", {"pass": 1}, commit=SHA_A), e("check", "t", {"pass": 1, "role": "author"}, session="s3", commit=SHA_A), e("review", "t", {"verdict": "ready"}, commit=SHA_A),
                    e("review", "t", {"verdict": "ready", "role": "author"}, session="s2", host="h2", commit=SHA_A)], "SUBMIT")]
        for evs, expected in ladder:
            self.assertEqual(self.view([cm("t")] + base, evs).fields["next"], expected)

    def test_activity_does_not_renew_claim(self):
        old = [e("claim", "t", seq=1, at="2026-10-21T00:00:00+00:00"),
               e("touch", "t", seq=2, at="2026-10-23T19:00:00+00:00"),
               e("check", "t", {"pass": 1}, seq=3, at="2026-10-23T19:10:00+00:00"),
               e("review", "t", {"verdict": "ready"}, seq=4, at="2026-10-23T19:20:00+00:00")]
        self.assertEqual(self.view([cm("t")], old).fields["claim_health"], "EXPIRED")

    def test_clock_skew_finding_and_not_trusted(self):
        future = [e("claim", "t", seq=1, at="2026-10-24T20:00:00+00:00")]
        v = self.view([cm("t")], future)
        self.assertIn("CLOCK_SKEW", [f.code for f in v.findings])
        self.assertEqual(v.fields["claim_health"], "FREE")
        ok = [e("claim", "t", seq=1, at="2026-10-23T20:01:00+00:00")]     # 1 min ahead: within tolerance
        self.assertNotIn("CLOCK_SKEW", [f.code for f in self.view([cm("t")], ok).findings])

    def test_nonowner_commit_finding(self):
        evs = [e("claim", "t", seq=1, at="2026-10-23T18:00:00+00:00"),
               e("touch", "t", {"tool": "Edit"}, session="s9", alias="h2·other", host="h2", seq=1,
                 at="2026-10-23T19:00:00+00:00")]
        self.assertIn("NONOWNER_EDIT", [f.code for f in self.view([cm("t")], evs).findings])
        review_only = [e("claim", "t", seq=1, at="2026-10-23T18:00:00+00:00"),
                       e("review", "t", {"verdict": "ready"}, session="s9", host="h2", seq=1, commit=SHA_B,
                         at="2026-10-23T19:00:00+00:00")]
        self.assertNotIn("NONOWNER_EDIT", [f.code for f in self.view([cm("t")], review_only).findings])
        bash_touch = [e("claim", "t", seq=1, at="2026-10-23T18:00:00+00:00"),
                      e("touch", "t", {"tool": "Bash"}, session="s9", host="h2", seq=1, at="2026-10-23T19:00:00+00:00")]
        self.assertNotIn("NONOWNER_EDIT", [f.code for f in self.view([cm("t")], bash_touch).findings])
        v = self.view([cm("t")], evs)
        self.assertEqual((v.fields["group"], v.fields["next"]), ("ATTENTION", "RESOLVE ownership"))

    def test_clock_skew_routes_to_attention(self):
        v = self.view([cm("t")], [e("touch", "t", seq=1, at="2026-10-25T00:00:00+00:00")])
        self.assertEqual((v.fields["group"], v.fields["next"]), ("ATTENTION", "CHECK clock"))

    def test_assign_alone_is_not_liveness(self):
        evs = [e("assign", "t", {"to_session": "s2", "to_alias": "h2·x"}, seq=1)]
        self.assertEqual(self.view([cm("t")], evs).fields["claim_health"], "FREE")
        after_expired = [e("claim", "t", seq=1, at="2026-10-21T00:00:00+00:00"),
                         e("assign", "t", {"to_session": "s1"}, seq=2, at="2026-10-23T19:00:00+00:00")]
        self.assertEqual(self.view([cm("t")], after_expired).fields["claim_health"], "EXPIRED")

    def test_head_newer_than_server_is_finding(self):
        obs = [cm("t"), gt("t", head_time="2026-10-23T10:00:00+00:00"), repo({SHA_S: "2026-10-22T00:00:00+00:00"})]
        v = self.view(obs)
        self.assertIn("HEAD≠SERVER", [f.code for f in v.findings])
        self.assertEqual(v.fields["sync"], "HEAD≠SERVER")
        self.assertEqual((v.fields["group"], v.fields["next"]), ("ATTENTION", "RERUN server"))

    def test_head_older_than_server_is_ok(self):
        obs = [cm("t"), gt("t", head_time="2026-10-21T00:00:00+00:00"), repo({SHA_S: "2026-10-22T00:00:00+00:00"})]
        self.assertEqual(self.view(obs).fields["sync"], "OK")

    def test_server_saw_head_readme_only_is_ok(self):
        obs = [cm("t", head_commit_sha=SHA_A), gt("t", head=SHA_A, head_time="2026-10-23T10:00:00+00:00", changed=["t/README.md"]),
               repo({SHA_S: "2026-10-22T00:00:00+00:00", SHA_A: "2026-10-23T10:00:00+00:00"})]
        v = self.view(obs)
        self.assertEqual(v.fields["sync"], "OK·doc")
        self.assertEqual(v.findings, [])

    def test_server_saw_head_code_changed_is_stale_valid(self):
        obs = [cm("t", head_commit_sha=SHA_A), gt("t", head=SHA_A, head_time="2026-10-23T10:00:00+00:00",
                                                     changed=["t/tests/test.sh"]),
               repo({SHA_S: "2026-10-22T00:00:00+00:00", SHA_A: "2026-10-23T10:00:00+00:00"})]
        v = self.view(obs)
        self.assertEqual(v.fields["sync"], "STALE_VALID")
        self.assertEqual(v.fields["next"], "RERUN server")

    def test_equal_heads_never_head_ne_server_even_without_times(self):
        obs = [cm("t", head_commit_sha=SHA_A), gt("t", head=SHA_A, head_time="2026-10-23T10:00:00+00:00",
                                                     changed=["t/src.py"]), repo({})]
        v = self.view(obs)
        self.assertNotIn("HEAD≠SERVER", [f.code for f in v.findings])
        self.assertEqual(v.fields["sync"], "STALE_VALID")

    def test_unequal_heads_never_stale_valid(self):
        obs = [cm("t", head_commit_sha=SHA_B), gt("t", head=SHA_A, head_time="2026-10-21T00:00:00+00:00",
                                                     changed=["t/src.py"]),
               repo({SHA_B: "2026-10-22T00:00:00+00:00"})]
        v = self.view(obs)
        self.assertNotIn("STALE_VALID", [f.code for f in v.findings])
        self.assertEqual(v.fields["sync"], "OK")

    def test_running_validation_on_other_commit_is_info_finding(self):
        v = self.view([cm("t", valid="pending", validation_commit_sha=SHA_B)])
        f = [x for x in v.findings if x.code == "VALID≠SERVER"]
        self.assertEqual(f[0].severity, "info")
        self.assertEqual(v.fields["next"], "WAIT validation")

    def test_validation_on_older_commit_finding(self):
        v = self.view([cm("t", validation_commit_sha=SHA_B)])
        self.assertIn("VALID≠SERVER", [f.code for f in v.findings])

    def test_disagreement_is_finding_not_overwrite(self):
        v = self.view([cm("t", validation_commit_sha=SHA_B)])
        self.assertEqual(v.fields["valid"], "PASS")       # server's word kept; the drift is a finding

    def test_failing_validation_attention(self):
        v = self.view([cm("t", valid="failed")])
        self.assertEqual((v.fields["group"], v.fields["next"]), ("ATTENTION", "FIX validation"))

    def test_done_not_available(self):
        v = self.view([cm("t", "archived")])
        self.assertEqual(v.fields["group"], "DONE")
        self.assertEqual(v.fields["owner"], "")

    def test_claim_owner_alias_and_expiry(self):
        obs = [cm("t")]
        evs = [e("alias", None, {"alias": "h1·lane loop"}, seq=1), e("claim", "t", seq=2, at="2026-10-23T19:00:00+00:00")]
        self.assertEqual(self.view(obs, evs).fields["owner"], "h1·lane loop")
        old = [e("claim", "t", seq=1, at="2026-10-21T00:00:00+00:00")]
        self.assertEqual(self.view(obs, old).fields["claim_health"], "EXPIRED")

    def test_release_frees(self):
        evs = [e("claim", "t", seq=1), e("release", "t", seq=2)]
        self.assertEqual(self.view([cm("t")], evs).fields["claim_health"], "FREE")

    def test_conflicting_live_claims(self):
        evs = [e("claim", "t", seq=1), e("claim", "t", session="s9", alias="h2·other", host="h2", seq=1)]
        v = self.view([cm("t")], evs)
        self.assertIn("CONFLICT", [f.code for f in v.findings])
        self.assertEqual(v.fields["next"], "RESOLVE CONFLICT")

    def test_check_stale_on_new_commit(self):
        obs = [cm("t"), gt("t", head=SHA_B), repo({})]
        evs = [e("check", "t", {"pass": 20, "warn": 2, "fail": 0}, commit=SHA_A)]
        v = self.view(obs, evs)
        self.assertEqual(v.fields["check"], "P20 W2 F0")
        self.assertTrue(v.fields["check_stale"])

    def test_pushes_split_at_submission(self):
        times = ["2026-10-23T00:00:00+00:00", "2026-10-22T00:00:00+00:00", "2026-10-18T00:00:00+00:00", "2026-10-17T00:00:00+00:00"]
        obs = [cm("t", "needs_revision", entered_pool_at="2026-10-20T00:00:00Z", reviewed_at="2026-10-21T00:00:00Z"),
               gt("t", times=times, head_time=times[0]), repo({SHA_S: "2026-10-23T12:00:00+00:00"})]
        v = self.view(obs)
        self.assertEqual((v.fields["pushes_before_submit"], v.fields["pushes_after_submit"]), (2, 2))
        self.assertEqual(v.fields["pushes"], "2+2")

    def test_next_priority_draft_ladder(self):
        obs = [cm("t"), gt("t"), repo({SHA_S: "2026-10-22T00:00:00+00:00"})]
        self.assertEqual(self.view(obs).fields["next"], "RUN check")
        one_check = [e("check", "t", {"pass": 20, "warn": 0, "fail": 0}, commit=SHA_A)]
        self.assertEqual(self.view(obs, one_check).fields["next"], "RUN check")      # independent only; author missing
        with_check = one_check + [e("check", "t", {"pass": 20, "warn": 0, "fail": 0, "role": "author"}, session="s3", commit=SHA_A)]
        self.assertEqual(self.view(obs, with_check).fields["next"], "GET R1")
        failing = with_check + [e("check", "t", {"pass": 1, "fail": 2}, session="s4", commit=SHA_A, seq=9,
                                  at="2026-10-23T19:30:00+00:00")]
        self.assertEqual(self.view(obs, failing).fields["next"], "FIX check")        # a later failure is not hidden

    def test_waiting_states(self):
        self.assertEqual(self.view([cm("t", "being_reviewed")]).fields["next"], "WAIT reviewer")
        self.assertEqual(self.view([cm("t", valid="pending")]).fields["next"], "WAIT validation")

    def test_age_uses_state_timestamp(self):
        v = self.view([cm("t", "needs_revision", reviewed_at="2026-10-22T20:00:00Z")])
        self.assertEqual(v.fields["state_age_s"], 86400)
        self.assertEqual(v.fields["age_level"], "warn")      # needs_revision warns after 24h


class LegacyOwnerTest(ProjectionTest):
    def test_legacy_note_shows_until_real_claim(self):
        note = e("note", "t", {"legacy_owner": "host-b", "status": "ACTIVE", "updated": "2026-10-22"}, seq=1)
        v = self.view([cm("t")], [note])
        self.assertEqual((v.fields["claim_health"], v.fields["owner"]), ("LEGACY", "host-b (CLAIMS.md)"))
        claimed = [note, e("claim", "t", seq=2)]
        self.assertEqual(self.view([cm("t")], claimed).fields["claim_health"], "OWNED")
        old = e("note", "t", {"legacy_owner": "host-b", "status": "ACTIVE", "updated": "2026-10-01"}, seq=1)
        self.assertEqual(self.view([cm("t")], [old]).fields["claim_health"], "FREE")


class ParkedTest(ProjectionTest):
    def test_parked_draft_leaves_todo_and_is_not_free(self):
        note = e("note", "t", {"legacy_owner": "host-b", "status": "PARKED", "updated": "2026-10-20"}, seq=1)
        f = self.view([cm("t", valid="failed")], [note]).fields
        self.assertEqual((f["group"], f["next"], f["tag"]), ("DONE", "PARKED", "Parked"))
        self.assertNotIn(f["ownership_state"], ("available", "never_seen"))

    def test_hold_row_and_parking_release_both_park(self):
        hold = e("note", "t", {"legacy_owner": "host-b", "status": "HOLD", "updated": "2026-10-20"}, seq=1)
        self.assertEqual(self.view([cm("t", valid="failed")], [hold]).fields["next"], "PARKED")
        rel = e("release", "t", {"reason": "parked: step 3 saturated"}, seq=1, at="2026-10-22T10:00:00+00:00")
        self.assertEqual(self.view([cm("t", valid="failed")], [rel]).fields["next"], "PARKED")
        plain = e("release", "t", {"reason": "done for today"}, seq=1, at="2026-10-22T10:00:00+00:00")
        self.assertNotEqual(self.view([cm("t", valid="failed")], [plain]).fields["next"], "PARKED")

    def test_stale_checkin_does_not_revive_parked(self):
        note = e("note", "t", {"legacy_owner": "host-b", "status": "PARKED", "updated": "2026-10-20"}, seq=1)
        old = e("presence", "t", {"last_seen": NOW.timestamp() - 9 * 3600, "checkin": True}, seq=2,
                at="2026-10-23T11:00:00+00:00")
        self.assertEqual(self.view([cm("t", valid="failed")], [note, old]).fields["next"], "PARKED")

    def test_work_after_parking_revives_it(self):
        note = e("note", "t", {"legacy_owner": "host-b", "status": "PARKED", "updated": "2026-10-20"}, seq=1)
        touch = e("presence", "t", {"last_seen": NOW.timestamp() - 60}, seq=2, at="2026-10-23T19:59:00+00:00")
        self.assertNotEqual(self.view([cm("t", valid="failed")], [note, touch]).fields["next"], "PARKED")


class Step13ProjectionTest(ProjectionTest):
    def test_own_agent_release_frees_advisory_owner(self):
        evs = [e("claim", "t", seq=1),
               e("release", "t", {"released_owner": {"session_id": "s1"}}, session="human:p@h1", seq=2)]
        self.assertEqual(self.view([cm("t")], evs).fields["claim_health"], "FREE")

    def test_git_only_task_shows_ref_owner(self):
        claim = Observation("claims", "t", NOW, {"claims.session_id": "s1", "claims.alias": "h1·x",
                                                 "claims.renewed_at": "2026-10-23T19:00:00+00:00"})
        views = {v.entity_id: v for v in project([gt("t"), claim], [], self.cfg, NOW, claims_healthy=True)}
        self.assertEqual((views["t"].fields["claim_health"], views["t"].fields["owner"]), ("OWNED", "h1·x"))


class RenewKeepsForeignEditTest(ProjectionTest):
    def test_ledger_claim_edit_renew(self):
        evs = [e("claim", "t", seq=1, at="2026-10-23T17:00:00+00:00"),
               e("touch", "t", {"tool": "Write"}, session="s9", host="h2", seq=1, at="2026-10-23T18:00:00+00:00"),
               e("renew", "t", seq=2, at="2026-10-23T19:00:00+00:00")]
        self.assertIn("NONOWNER_EDIT", [f.code for f in self.view([cm("t")], evs).findings])

    def test_ref_claim_edit_renew(self):
        claim = Observation("claims", "t", NOW, {"claims.session_id": "s1", "claims.alias": "h1·x",
                                                 "claims.acquired_at": "2026-10-23T17:00:00+00:00",
                                                 "claims.renewed_at": "2026-10-23T19:00:00+00:00"})
        evs = [e("touch", "t", {"tool": "Edit"}, session="s9", host="h2", seq=1, at="2026-10-23T18:00:00+00:00")]
        views = {v.entity_id: v for v in project([cm("t"), claim], evs, self.cfg, NOW, claims_healthy=True)}
        self.assertIn("NONOWNER_EDIT", [f.code for f in views["t"].findings])

    def test_legacy_expiry_from_note(self):
        long = e("note", "t", {"legacy_owner": "host-b", "status": "ACTIVE", "updated": "2026-10-01", "expires_at": "2026-11-01T00:00:00+00:00"}, seq=1)
        self.assertEqual(self.view([cm("t")], [long]).fields["claim_health"], "LEGACY")
        short = e("note", "t", {"legacy_owner": "host-b", "status": "ACTIVE", "updated": "2026-10-23", "expires_at": "2026-10-23T12:00:00+00:00"}, seq=1)
        self.assertEqual(self.view([cm("t")], [short]).fields["claim_health"], "FREE")


class CodexFindingsTest(ProjectionTest):
    def test_latest_verdict_per_session_wins(self):
        obs = [cm("t"), gt("t"), repo({SHA_S: "2026-10-22T00:00:00+00:00"})]
        evs = [e("review", "t", {"verdict": "ready"}, commit=SHA_A, seq=1, at="2026-10-23T18:00:00+00:00"),
               e("review", "t", {"verdict": "changes"}, commit=SHA_A, seq=2, at="2026-10-23T19:00:00+00:00"),
               e("review", "t", {"verdict": "ready", "role": "author"}, session="s2", host="h2", commit=SHA_A, seq=1)]
        v = self.view(obs, evs)
        self.assertEqual(v.fields["review"], "R1")
        self.assertEqual(v.fields["dissent"], 1)

    def test_claimed_new_slug_is_visible(self):
        evs = [e("claim", "brand-new-slug", seq=1)]
        views = {v.entity_id: v for v in project([cm("t")], evs, self.cfg, NOW)}
        self.assertIn("brand-new-slug", views)
        self.assertEqual(views["brand-new-slug"].fields["claim_health"], "OWNED")


class AuditFixesTest(ProjectionTest):
    def test_historical_legacy_status_is_not_ownership(self):
        n = e("note", "t", {"legacy_owner": "host-b", "status": "PUSHED", "updated": "2026-10-23",
                            "expires_at": "2026-10-30T00:00:00+00:00"}, seq=1)
        self.assertEqual(self.view([cm("t")], [n]).fields["claim_health"], "FREE")

    def test_stale_results_rerun_before_fix(self):
        obs = [cm("t", valid="failed", head_commit_sha=SHA_B), gt("t", head=SHA_A, head_time="2026-10-23T12:00:00+00:00"),
               repo({SHA_B: "2026-10-22T00:00:00+00:00"})]
        self.assertEqual(self.view(obs).fields["next"], "RERUN server")

    def test_audit_doc_change_is_doc_only(self):
        obs = [cm("t", head_commit_sha=SHA_A), gt("t", head=SHA_A, changed=["t/audit/REVIEW-LEDGER.md", "t/README.md"]),
               repo({SHA_A: "2026-10-21T00:00:00+00:00"})]
        self.assertEqual(self.view(obs).fields["sync"], "OK·doc")

    def test_current_agent_dissent_comes_first(self):
        obs = [cm("t"), gt("t"), repo({SHA_S: "2026-10-22T00:00:00+00:00"})]
        evs = [e("review", "t", {"verdict": "changes", "confidence": 4}, commit=SHA_A)]
        self.assertEqual(self.view(obs, evs).fields["next"], "ADDRESS agent review")

    def test_draft_age_label_honest(self):
        v = self.view([cm("t", entered_pool_at="2026-10-10T00:00:00Z", updated_at="2026-10-23T10:00:00Z")])
        self.assertEqual(v.fields["age_label"], "back in draft since (approx.)")
        self.assertEqual(v.fields["state_age_s"], 10 * 3600)


class NeedsRevisionProgressTest(ProjectionTest):
    def test_pushes_after_request_move_to_ladder(self):
        base = dict(entered_pool_at="2026-10-20T00:00:00Z", reviewed_at="2026-10-21T00:00:00Z")
        repo_ = repo({SHA_S: "2026-10-22T00:00:00+00:00"})
        idle = self.view([cm("t", "needs_revision", **base), gt("t", head_time="2026-10-20T12:00:00+00:00"), repo_])
        self.assertEqual(idle.fields["next"], "ADDRESS review")
        pushed = [cm("t", "needs_revision", **base), gt("t", times=["2026-10-22T00:00:00+00:00"], head_time="2026-10-22T00:00:00+00:00"), repo_]
        v = self.view(pushed)
        self.assertEqual((v.fields["pushes_since_decision"], v.fields["next"]), (1, "RUN check"))
        done = [e("check", "t", {"pass": 1}, commit=SHA_A), e("check", "t", {"pass": 1, "role": "author"}, session="s3", commit=SHA_A),
                e("review", "t", {"verdict": "ready"}, commit=SHA_A),
                e("review", "t", {"verdict": "ready", "role": "author"}, session="s2", host="h2", commit=SHA_A)]
        self.assertEqual(self.view(pushed, done).fields["next"], "RESUBMIT")
        self.assertEqual(self.view(pushed).fields["tag"], "Needs revision")
