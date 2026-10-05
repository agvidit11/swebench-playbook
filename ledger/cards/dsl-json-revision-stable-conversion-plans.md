# dsl-json-revision-stable-conversion-plans

- Date/machine: 2026-10-05 / devvm23237
- Repo/base: `ngs-doo/dsl-json` @ `b40f8160659de9bea66b40d0a753c7a9a9795e01` (newest green commit before unrelated HEAD regression)
- Seam: immutable root conversion plan -> isolated leaf overrides -> complete transform round-trip
- Trap: natural order loses configuration coherence through cached dependent converters
- Routing: `MEASURE`, three fresh-session K-to-N steps
- A4: `CLEAR`; no converter-plan/profile/snapshot task or disclosed remedy found

## User problem and base evidence

Services use different JSON spellings for the same Java types. Today a leaf converter change can affect direct values while previously resolved lists, maps, optionals, or generated objects keep an older converter. I need a stable per-partner conversion plan that I can safely derive and use for a complete transformation without changing the shared `DslJson` instance.

At the pinned base, registering a new direct `Item` writer changed direct output while an already-resolved `List<Item>` writer still emitted the old form. The same stale split reproduced for readers. Removing a class override through the `Type` overload also lost an inherited writer because the class mapping remained in `writerMap`. All three focused reproductions pass offline in 0.119 seconds; the full library suite passes 1,792/1,792.

## Steps

1. Capture an immutable conversion plan for a root `Type`, resolving one coherent reader/writer/binder graph.
2. Derive an isolated plan with selected leaf converter overrides. Dependent generic, runtime, and generated converters consistently follow the override while the source and earlier plans remain unchanged.
3. Use the derived plan for a distinct decode -> transform -> encode -> redecode operation without consulting or mutating the live registry.

CONSTRAINT: freeze a coherent dependent converter graph, derive it with copy-on-write semantics, then perform the whole transformation through that authority.

NON-DESIRED: shallow registry-map copies; leaf-only overrides; dependent converters captured from a different revision; fallback to the live `DslJson`; mutating the source plan or global registry; fixing only read or only write.

Independent branches include collection/map/optional dependency capture, generated converter capture, read/write asymmetry, inherited fallback removal, runtime types, and live-registry isolation. Step 3 is a distinct end-to-end transformation operation and can independently miss decoding, encoding, or isolation. No single-turn fallback.

Relevant seams: `DslJson.java:934-1148`, `CollectionAnalyzer.java:124-144`, `MapAnalyzer.java:101-132`, `OptionalAnalyzer.java:48-80`, and generated capture in `ConverterTemplate.java:227-264`.

Evidence: `/root/scout_dsl_json` handoff.

Rating: P1 4, P2 4, P3 2, P4 3, P5 4, P6 3, P7 3 = **23/28 MEASURE**.
