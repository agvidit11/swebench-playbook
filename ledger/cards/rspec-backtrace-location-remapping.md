# rspec-backtrace-location-remapping

- Date/machine: 2026-10-02 / devvm23237
- Repo/base: `rspec/rspec` @ `df877b73ab2a01bc7e3b5a39e7e252e8d9bb67a3`
- Seam: `rspec-core/lib/rspec/core/backtrace_formatter.rb`
- Composition: closed extension point × state preserved across a transform boundary
- Trap: natural order loses information
- Routing: `MEASURE` in Lane P
- A4: `ADJACENT`; Errbit source maps and native symbolicators are different seams

## User problem

I maintain an RSpec adapter for a template/compiler framework. Exceptions point into generated Ruby, but the adapter knows the corresponding template/spec locations. RSpec only lets me filter raw backtrace strings, so generated frames may disappear before I can turn them into useful user locations. I need a lossless frame representation and a formatter-local mapping extension that remaps locations before RSpec applies its normal inclusion and exclusion rules.

## Base evidence

At the pinned base, `BacktraceFormatter#format_backtrace` filters raw strings before relative-path conversion. A generated `/work/generated/views/account.rb:12` frame was dropped by an exclusion pattern, leaving only `/work/lib/runner.rb:44`; no mapper API exists. `BacktraceFormatter#filter_gem` adds exclusion patterns but no transformation stage.

## Obligations

CONSTRAINT: Registered backtrace location mappers receive losslessly parsed frames and run before relative-path conversion and inclusion/exclusion filtering, so mapped user frames survive, mapped excluded frames are removed, and unmapped or opaque lines retain existing behavior.

DESIRED: A round-trippable frame value followed by a formatter-local mapping pipeline whose output, not the generated input, is filtered.

NON-DESIRED: Filter-before-map; naive colon splitting; regex-only rewriting; loss of labels or Windows drive prefixes; process-global mapper state; full-backtrace mapping bypass; fallback to raw generated frames after mapped frames are filtered.

## Step 1 — lossless backtrace frames

Introduce immutable `BacktraceFormatter::Frame.parse(String)` with `path`, `line_number`, `label`, `raw`, `with_location(path, line_number)`, and `to_s`. Ordinary lines round-trip byte-for-byte until changed; labels and Windows drive paths survive; opaque lines round-trip; `with_location` changes only path/line. Existing behavior is unchanged without mappers.

Expected production delta: 65–100 lines plus specs.

## Step 2 — mapping before filtering

Expose formatter-local ordered `location_mappers`. Each callable receives a Step-1 frame and returns a replacement or `nil`. Chaining, exception propagation, relative-path normalization, inclusion/exclusion, `full_backtrace`, all-filtered fallback, and legacy empty-list behavior must observe the final mapped frame.

Step 2 owns Step-1 guards for POSIX/Windows/opaque round trips, labels containing colons, nil mappings, chaining, mapped-to-excluded, excluded-raw-to-user, full-backtrace, and fallback. Step-1 gold cannot satisfy Step 2.

Expected production delta: 45–75 lines plus specs.

## Review receipt

Wrong branches: filter-then-map, naive colon split, full-backtrace bypass, raw fallback, global registry, swallowed mapper exceptions. Pure deterministic in-memory grading.

Six disclosure-query families across `rspec/rspec` and historical `rspec-core` found no frame-mapping cause/remedy. RSpec core issue 1221 only recommends full backtraces and does not propose parsing/remapping. No peer uses this RSpec seam.

Rating: P1 4, P2 2, P3 1, P4 3, P5 4, P6 3, P7 2 = **19/28 MEASURE**. Primary probe risk: a solver may bypass the frame object with string substitution while satisfying Step-2 observables.

