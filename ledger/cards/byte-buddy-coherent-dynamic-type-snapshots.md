# byte-buddy-coherent-dynamic-type-snapshots

- Date/machine: 2026-10-05 / devvm23237
- Repo/base: `raphw/byte-buddy` @ `807fb56674daf54d8bb01a578e84bac4130b5e1c`
- Seam: coherent dynamic-type family snapshot -> explicit replacement -> publish/reload
- Trap: flattening loses duplicate provenance across lookup, inspection, and persistence
- Routing: `MEASURE`, three fresh-session K-to-N steps
- A4: `CLEAR`; no dynamic-family snapshot/replacement/conflict peer or disclosed remedy found

## User problem and base evidence

I assemble related generated classes in stages. Byte Buddy can currently inspect one version of a class but load or write another, and a later redefinition can disappear when I add the rest of the generated family back. I need a stable family snapshot that I can update deliberately and publish, so the class I inspect is the class actually reloaded, with generic shape, annotations, supporting classes, and behavior intact.

At base, a family with two `survey.Duplicate` definitions made `locate()` return the first definition while `getAllTypes()` paired the first description key with the second definition's bytes, and `load()`/`toJar()` used the second definition. The first declared `T extends Number` and annotation `first`; the loaded class had `T extends CharSequence` and annotation `second`. Redefinition produced `transformed`, but `.include(oldFamily)` silently reverted it to `second`. Raw bytes are also mutable through `getBytes()`. Three runs were byte-identical.

## Steps

1. Add `DynamicType.Unloaded<T>#snapshot(ClassFileLocator dependencies)` returning a coherent `DynamicType.Snapshot<T>`. Bytes are defensive, type descriptions come from those same bytes, identical duplicate names coalesce, differing duplicates fail, and families with live loaded-type initializers are refused.
2. Add explicit `Snapshot<T>#replace(...)` operations. Replacements win by binary name, unrelated primary/auxiliary types remain, and the source snapshot is unchanged. Redefine/rebase can use the snapshot as its locator.
3. Ensure inherited locator/maps/load/directory/JAR/injection/reload paths consume the same derived family. Generate -> snapshot -> redefine/rebase -> replace -> write -> reload preserves behavior, annotations, generics, method graph, and auxiliary types.

CONSTRAINT: one normalized family authority must drive inspection, transformation, lookup, loading, and persistence.

NON-DESIRED: first-wins lookup plus last-wins bytes; shallow raw byte capture; duplicate overwrite without validation; implementing replacement as append/include; output paths that reflatten independently; persisting live initializer state as null behavior.

Independent branches include differing duplicate bytes, equal duplicates, byte defensiveness, stale description keys, replacement masking, auxiliary retention, locator dependency resolution, generic/annotation fidelity, and load/JAR/reload parity. Step 3 is distinct publication/reload consuming the derived snapshot. No single-turn fallback.

Evidence: `/tmp/byte-buddy-lanei-20261005/SurveyRepro.java` and `/root/scout_byte_buddy` handoff.

Rating: P1 4, P2 4, P3 2, P4 3, P5 4, P6 3, P7 3 = **23/28 MEASURE**.
