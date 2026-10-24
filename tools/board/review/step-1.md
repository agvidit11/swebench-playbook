# Step 1 review

## 1) VERDICT: CHANGES

The reviewed code is stdlib-only, and no private identity, host, path, repository, reviewer, or internal URL values are embedded in it. Task 1 is not ready to approve because the example configuration does not load faithfully and two interfaces promised to later tasks are absent.

Requested test command: `python3 -m unittest discover -s tests -v`

```text
Ran 12 tests in 0.002s

FAILED (errors=1)
```

The one error is `test_events (unittest.loader._FailedTest.test_events)`: the out-of-scope `tests/test_events.py` imports `workboard.events`, which does not exist yet. The 11 loaded Task 1 config/registry tests passed.

## 2) Required changes

1. `workboard/config.py:110-126` — Apply `_INTERNAL = {"path", "warnings"}` only while filling the root `Config`, not every nested dataclass. As written, both `repositories[0].path` and `ledger.path` are classified as unknown and silently retain their defaults; loading `config.example.toml` proves this (`repository.path == ""`, plus warnings for both paths). Build `known` with the exclusion only when `obj` is the root `Config` (or mark root-only fields with dataclass metadata), and add regression assertions that repository and ledger paths load without warnings.

2. `workboard/config.py:88-103` — Add the plan-required `reports` configuration section. Define a `Reports` dataclass containing at least `include_contribution: bool = False` from DESIGN.md section 10, add `reports: Reports = field(default_factory=Reports)` to `Config`, document it in `config.example.toml`, and test both its default and TOML override. Later report/export code is specified to consume this API.

3. `workboard/model.py:55-59` — Restore the promised `TaskView(entity_id, fields, findings, health)` shape by adding `health: dict = field(default_factory=dict)`. Also type the existing containers (`fields: dict[str, object]`, `findings: list[Finding]`, and the appropriate health value type) so projection and renderer consumers share an explicit contract. Add a construction/default-isolation test.

4. `workboard/model.py:30-34` — Make `Finding.next_action` a required `str`, rather than an optional field defaulting to `None`. The Task 1 interface lists it as a required constructor argument, and DESIGN.md says findings have a next action. Add tests for the full constructor and invalid severities so later producers cannot create findings that render without remediation guidance.

5. `workboard/config.py:118-136` — Validate collection contents and exact scalar types, not only the type of each default object. The current loader accepts `expire_after_hours = true` because `bool` is an `int`, accepts non-string plugin IDs, and accepts non-numeric threshold values; a scalar member of `servers`/`repositories` leaks an `AttributeError` instead of a dotted-path `ValueError`. Use the declared field types (for example `list[str]`, `list[Server]`, and `dict[str, int]`) for recursive validation, explicitly exclude `bool` from integer fields, require every array-of-tables element to be a table, and add one test for each malformed shape.

## 3) Optional suggestions

1. `workboard/registry.py:17-23,37-40` — Reject duplicate names within a kind, including collisions across enabled plugins, instead of silently letting the last plugin win; include both the kind and name in the warning.

2. `workboard/config.py:91` — Either make `swebench-codimango` the default profile or document why missing-config defaults intentionally use `default`; DESIGN.md currently calls `swebench-codimango` the default profile for this deployment.

3. `tests/test_config.py:6-10` and `tests/test_registry.py:7-12` — Use managed temporary directories and remove injected fake modules in cleanup to keep the test process isolated as this suite grows.
