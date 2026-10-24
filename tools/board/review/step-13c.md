# Step 13c re-check (step-13b items 1–6 only)

## 1) VERDICT: CHANGES

Items 1, 2, and 5 are functionally fixed, and the core fixes for items 3 and 4 are present. The implementation
remains stdlib-only. It is not ready to approve: setup can destroy an unrelated symlink, normalized rank labels
can retain surrounding whitespace despite the requested strip contract, and the tracked-file privacy scan is not
clean because `review/step-13b.md` reintroduces the two personal paths that item 6 required removing. No
`review/*.log` file is tracked, and `.gitignore` excludes those logs; no untracked log was read.

Requested command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 403 tests in 67.970s

OK
```

## 2) Required changes

1. `workboard/__main__.py:780-790` and `tests/test_cli.py:479-496` — Do not replace an unrelated symlink during
   setup. `link()` currently unlinks every symlink whose literal target is not `src`, so a user's existing
   `~/.local/bin/board` or skill symlink can be destroyed; a subsequent `symlink_to()` failure also leaves it
   lost. Resolve and accept a symlink only when it points to the requested source; otherwise report a destination
   conflict and leave it untouched. Add wrong-symlink regressions for both the command and skill destinations,
   plus a relative symlink that resolves to the correct source.

2. `workboard/rank.py:43-44,64-74,84-106` and `tests/test_stats.py:230-245` — Complete item 3's normalization
   contract. `_row_ok()` checks stripped labels but `normalize()` returns the original `scope` and `window`, so
   direct JSON rows such as `" Org "` remain non-canonical and create distinct display/cache keys. Strip and store
   both labels for canonical and wide rows, rejecting them when empty, and add direct canonical/wide regressions
   that assert the normalized values rather than only rejection of whitespace-only labels. Also treat only an
   already-normalized null as null in `_num()`; convert empty CSV/rank cells to `None` before calling it instead of
   silently converting arbitrary raw whitespace strings to null.

3. `review/step-13b.md:61-64` — Complete item 6's tracked-file scrub. This review text itself names the private
   ledger relative path and personal tool-directory prefix that it says to remove, so the scan over all 74 paths
   returned by `git ls-files -- .` is not clean. Replace both literals with neutral wording such as
   “the prior hard-coded ledger and personal tool paths,” then rerun the scan over every tracked file. Keep the
   existing tracked-log check; it is currently clean.

## 3) Optional suggestions

None.
