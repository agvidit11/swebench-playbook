# picocli-detached-parse-overlay-execution

- Date/machine: 2026-10-05 / devvm23237
- Repo/base: `remkop/picocli` @ `10509c0af89aa3254ca14ba90d9b3b7168e57994`
- Seam: detached parse observations -> profile overlay -> execution from frozen values
- Trap: natural order loses information across shared mutable `ArgSpec` and user-object state
- Routing: `MEASURE`, three fresh-session K-to-N steps
- A4: `ADJACENT`; 18 direct picocli peer seams excluded, no historical-result/overlay peer found

## User problem and base evidence

My application prepares command invocations before running them. When it parses another invocation, an earlier result silently changes and can execute with the newer values. I need old results to stay fixed, combine saved settings with explicit later overrides, and execute that combined invocation reliably.

At base, a first parse changed from `tags=[red], count=1` to `tags=[blue], count=2` after a second parse. Executing the first result then ran with `count=2`. A failed parse also left already-consumed values on the bound object. `ParseResult` copies collections of mutable `ArgSpec` references, accessors read their current live values, parser reuse clears/repopulates them, and `RunLast` returns to the live command hierarchy.

## Steps

1. Results returned by `parseArgs` retain their original option, positional, group, and subcommand observations after parser reuse.
2. Add `public ParseResult overlay(ParseResult overrides)`: explicit override observations win and absent values retain the base. Compatible subcommand paths may extend one another; divergent paths fail with the existing `ParameterException`. Existing arity, group, and default rules still hold, and neither input changes.
3. Existing `public int RunLast.execute(ParseResult parseResult)` executes the overlaid result's frozen values after further parses without mutating either source result.

CONSTRAINT: detach historical observations, reconcile explicit provenance, then execute from the detached authority.

NON-DESIRED: shallow collection copies; raw-argument concatenation; losing explicit-versus-default provenance; merging divergent subcommand paths; mutating an input; accessors that look frozen while execution reaches current bound state.

Likely independent branches: list/map/array/group aliasing; defaulted values overwriting explicit base values; subcommand-path disagreement; overlay input mutation; `RunLast` using the latest command object. Step 3 is a distinct execution operation, not another snapshot/report operation. No single-turn fallback.

Base evidence and focused harness: `/tmp/picocli-lane-i-Zsuham`.

Rating: P1 4, P2 2, P3 2, P4 3, P5 4, P6 3, P7 3 = **21/28 MEASURE**.
