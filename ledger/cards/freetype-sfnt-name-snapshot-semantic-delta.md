# freetype-sfnt-name-snapshot-semantic-delta

- Date/machine: 2026-10-02 / devvm23237
- Repo/base: `freetype/freetype` @ `a3f35254a447374960db535d8fc044591b4da83f`
- Seam: `ftsnames.h`, `ftsnames.c`, existing SFNT-name enumeration API
- Composition: semantic identity distinct from serialization × snapshot versus borrowed view
- Trap: physical record order and borrowed storage lose logical identity/lifetime
- Routing: `MEASURE`, two chained steps
- A4: `ADJACENT`; no FreeType/SFNT-name task collision

## A1 and base proof

Eligible FreeType/GPL dual license; active 2026-10-02; ~250k non-test C/header LOC; no agent artifacts/identities; 70 open GitLab issues; offline build 5.46s. Target API's last functional change was 2021.

I compare font builds and repackaged fonts to decide whether human-facing name metadata changed. Current FreeType exposes physical records in table order backed by face-owned memory. Swapping the first/last 12-byte name records in the real `varc-null-condition.ttf` fixture preserved family, style, count, and the complete logical record set, but moved the same record from public index 0 to 19. No owned snapshot or semantic diff exists.

CONSTRAINT: Comparisons depend on distinct complete raw name records, not physical order or duplicate entries. Captured bytes survive face destruction; deltas report stable minimal additions/removals.

DESIRED: An owned canonical snapshot followed by an independently owned set delta.

NON-DESIRED: face-owned shallow pointers; table order; retained exact duplicates; positional comparison; transcoding/case-folding; face-to-face diff bypassing Step 1.

## Steps

1. `FT_Get_Sfnt_Name_Snapshot` creates an owned, duplicate-free snapshot ordered by `(name_id, platform_id, encoding_id, language_id, string_len, bytes)`. Identity includes all IDs, length and exact bytes. The snapshot remains valid after `FT_Done_Face`; failures leave output null and leak-free.
2. `FT_Diff_Sfnt_Name_Snapshots` returns independently owned canonical removed/added snapshots. Shared exact records disappear; a change is one removal plus one addition; reorder/duplicate-only changes are empty; reversal swaps sides; failures are atomic.

Pinned types/functions: `FT_SfntNameSnapshot`, get/done snapshot functions, `FT_SfntNameDiff`, diff/done functions, with public `num_names`, `names`, `removed`, `added` fields. Raw strings are uninterpreted bytes and lifetimes are library-owned.

Wrong shapes: shallow copy; source order; no dedup; text normalization; positional zip; diff borrowing inputs. Step 2 owns permutation, duplicate, byte/identifier change, destroyed-face/input lifetime, and deterministic allocator-failure guards.

Both steps incrementally touch the same header/body. Expected production deltas: 90–140 and 80–130 lines. Deterministic in-memory fixtures and custom allocator seam.

Exact GitLab searches found no snapshot/canonical-name/diff proposal. Rating: P1 4, P2 2, P3 2, P4 4, P5 4, P6 4, P7 3 = **23/28 MEASURE**. Probe risks: public-ABI narrowness, library-altitude fit, and whether Step 2 becomes mechanical after Step 1.

