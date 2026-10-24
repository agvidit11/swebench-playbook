# Step 3 review

## 1) VERDICT: CHANGES

The adapter is stdlib-only, uses argv-based subprocess calls, namespaces observations correctly, drops the large prose blobs, merges archived tasks, and contains no committed private values. Most task-2 corrections are also present. However, an incomplete response currently destroys the last-good snapshot, malformed envelopes/cache entries can escape the failure path, and one required event-schema validation remains incomplete.

Requested test command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 43 tests in 0.511s

OK
```

## 2) Required changes

1. `workboard/sources/codimango.py:120-132` and `tests/test_codimango.py:66-68` — Do not write or serve a `totalExact=false` response as the last-good snapshot. After both calls return, if either envelope is incomplete, retain and serve the prior complete cache, report `INCOMPLETE`, and mark source health unhealthy so the later `--strict` contract can fail. If no complete cache exists, return the partial observations only with explicit unhealthy/incomplete state. Add a regression that first caches two tasks, then returns one task with `totalExact=false`, and asserts that both the returned observations and cache still contain the two complete tasks. The current implementation serves one task, overwrites the cache with it, and reports `health.ok=True`.

2. `workboard/sources/codimango.py:53-62,120-126` — Implement the DESIGN §4 envelope/schema validation before normalization: require an object envelope, `tasks` as a list of task objects with usable string names, and actual booleans for `totalExact` and `trainingStatusDegraded`. Remove the bare-list/missing-field “exact” fallback and do not use `bool(...)` coercion. Any invalid active or archived envelope must follow `_failed(...)` and preserve/use the prior cache rather than raise. Add cases for missing flags, string `"false"` flags, and a scalar task entry; currently the first is accepted as healthy, the second is misread as true/degraded, and the third raises `AttributeError`.

3. `workboard/sources/codimango.py:77-82,111-114,134-157` — Validate the complete cache shape when reading it: a timezone-aware parseable `fetched_at`, boolean health flags, and normalized row dictionaries with string names. Treat any invalid cache as absent and never let it escape `_failed` or the fresh-cache path. Add failed-runner regressions for `{"rows": []}` and for a cache containing a scalar row; these currently raise `KeyError` and `AttributeError` instead of returning an empty unhealthy `FetchResult`.

4. `workboard/events.py:145-147` and `tests/test_events.py:85-93` — Finish step-2 required change 1 by requiring the actor fields to be present and valid. `all(isinstance(actor.get(k, ""), str) ...)` accepts an empty actor object because every missing key defaults to a string. Require string `session_id` and `alias`, and constrain `kind` to the schema values (`claude|codex|muse|human`); skip the bad row with `MALFORMED_EVENTS`. Add a parseable `{}`-actor row between valid neighbors.

5. `workboard/events.py:165-175` and `tests/test_events.py:108-114` — Finish the step-2 line-bound fix by treating every record whose bytes exceed `MAX_LINE` as oversized, including a `MAX_LINE + 1` read that already ends in `\n`. The current `len(line) > limit and not line.endswith(b"\n")` condition admits that boundary case. Drain only when needed, but always yield the oversize marker; add a boundary regression that asserts the finding says `oversize` and later valid events survive.

## 3) Optional suggestions

1. `workboard/sources/codimango.py:84-89` — Unlink the temporary cache file if serialization or replacement fails; otherwise failed writes leave `.cm-*.json` files behind.

2. `workboard/sources/codimango.py:22-28` — Drop `reviewerName` and `sourceRepo` unless a later interface demonstrably needs them. They are outside task 3's required field set and unnecessarily place private-category data in the cache.

3. `tests/test_codimango.py:25-27` — Use `TemporaryDirectory` with cleanup instead of leaking one `mkdtemp` directory per test.

4. `tests/test_codimango.py:32-43` — Keep separate, explicitly named regressions for stderr-banner handling, huge-prose dropping, and archived merging as listed in the plan; the combined happy-path test makes failures less diagnostic.
