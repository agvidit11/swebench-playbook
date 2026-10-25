import unittest

from workboard.roles import gates, role_of


def ev(type_, payload, session="s1", host="h1", seq=1, at="2026-10-23T10:00:00+00:00", commit="a" * 40):
    return {"type": type_, "payload": payload, "actor": {"session_id": session, "alias": f"{host}·x"},
            "host_id": host, "seq": seq, "occurred_at": at, "commit": commit}


class RolesTest(unittest.TestCase):
    def test_inference(self):
        claim = ev("claim", {}, session="builder")
        self.assertEqual(role_of(ev("check", {}, session="builder"), [claim]), "author")
        self.assertEqual(role_of(ev("check", {}, session="other"), [claim]), "independent")
        self.assertEqual(role_of(ev("check", {"summary": "§5d READY"}, session="builder"), [claim]), "independent")
        self.assertEqual(role_of(ev("check", {"role": "author"}, session="other"), [claim]), "author")

    def test_latest_check_is_chronological_across_servers(self):
        newer_on_a = ev("check", {"fail": 0}, host="a-host", seq=50, at="2026-10-23T12:00:00+00:00")
        older_on_z = ev("check", {"fail": 3}, host="z-host", seq=1, at="2026-10-23T09:00:00+00:00")
        g = gates([older_on_z, newer_on_a][::-1], {"a" * 40})          # (host, seq) order would pick z-host last
        self.assertEqual(g["independent"]["check"]["state"], "ok")

    def test_old_commit_keeps_glyph_info(self):
        g = gates([ev("check", {"fail": 2})], {"b" * 40})
        self.assertEqual((g["independent"]["check"]["state"], g["independent"]["check"]["fail"]), ("old", 2))


class RolesHardeningTest(unittest.TestCase):
    def test_one_session_cannot_fill_both_check_slots(self):
        evs = [ev("check", {"fail": 0, "role": "author"}, session="x"), ev("check", {"fail": 0, "role": "independent"}, session="x", seq=2)]
        g = gates(evs, {"a" * 40})
        self.assertEqual((g["author"]["check"]["state"], g["independent"]["check"]["state"]), ("ok", "none"))

    def test_later_claim_does_not_relabel_old_check(self):
        chk = ev("check", {"fail": 0}, session="fresh", at="2026-10-23T10:00:00+00:00")
        later = ev("claim", {}, session="fresh", at="2026-10-23T11:00:00+00:00")
        self.assertEqual(role_of(chk, [chk, later]), "independent")

    def test_marker_is_a_prefix_not_a_substring(self):
        claim = ev("claim", {}, session="b", at="2026-10-23T09:00:00+00:00")
        self.assertEqual(role_of(ev("check", {"summary": "not an independent review"}, session="b"), [claim]), "author")
        self.assertEqual(role_of(ev("check", {"summary": "independent: clean"}, session="b"), [claim]), "independent")
