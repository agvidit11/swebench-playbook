# Step 10b review

## 1) VERDICT: CHANGES

Prior items 1, 2, and 4 are fixed: every attempted gate records safe counts, failed/unparsed runs cannot appear
green, review mutation now fails closed around ledger synchronization, and malformed summary regexes are rejected
during config loading. The config default path is also correctly resolved at call time. The reviewed code remains
stdlib-only and contains no private values.

Prior item 3 is not fully correct. The live-output implementation corrupts a multibyte UTF-8 character when its
bytes cross a 4096-byte read boundary. It also keeps stdout and stderr in one shared parsing tail, so sufficiently
verbose stderr can evict a valid final stdout summary and turn a successful, parsed gate into a false failure.

Requested command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 227 tests in 58.860s

OK
```

## 2) Required changes

1. `workboard/checks.py:48-87` and `tests/test_checks.py:88-105` — Preserve streamed text across arbitrary pipe
   chunk boundaries and do not let stderr evict the stdout summary. Use one incremental UTF-8 decoder per stream
   (including a final decoder flush), and retain a bounded stdout tail independently for `parse_summary`; stderr
   should still pass through live but must not consume the stdout parsing budget. Add regressions that (a) place a
   multibyte character across the 4096-byte boundary and assert exact output, (b) emit a valid stdout summary
   followed by more than `TAIL_BYTES` on stderr and assert the recorded counts remain parsed, and (c) directly
   assert the text supplied to `parse_summary` is bounded. The current `test_tail_is_bounded` verifies passthrough
   and end-of-output parsing, but would also pass an implementation that retained the entire 500 KB output.

## 3) Optional suggestions

None.
