# rich-layout-subtree-snapshot-reconcile

- Date/machine: 2026-10-04 / devvm23237
- Repo/base: `Textualize/rich` @ `9d8f9a372cc5916fd4781fec207ced7ddac2f08f`
- Seam: nested `Layout.map` snapshots -> locality-preserving `refresh_screen` reconciliation
- Trap: natural order loses information; existing helper is too narrow
- Routing: `MEASURE`, two chained steps with continued-session probe
- A4: `ADJACENT`; no `Layout.refresh_screen` task or disclosed remedy

## User problem and base evidence

I have a dashboard made of nested panes. Updating one leaf works until I hide, move, or resize panes: asking Rich to refresh an enclosing pane crashes, and refreshing a surviving pane leaves it at its old width until I redraw the whole dashboard. I need Rich to remember what every pane last occupied and use that saved view to refresh a named pane without making unrelated panes flicker.

At base, nested `root/main/{left,right}` rendered map names `footer,left,right`, omitting `root` and `main`; refreshing `main` raised `KeyError`. After hiding `left`, partial refresh left `right` at x=10,width=10, while a full render moved it to x=0,width=20.

## Steps

1. After render, existing `Layout.map` is an immutable point-in-time snapshot for every visible node, including containers. Each container's `LayoutRender` records its region and composed cells. Mutating the tree cannot mutate a held prior map.
2. Extend existing `Layout.refresh_screen(..., previous=None)` so a supplied Step-1 snapshot reconciles the named subtree after visibility, membership, size, or ratio changes. Resulting screen equals a full render; vacated pixels are removed; unaffected sibling regions are not rewritten; calls without `previous` retain behavior.

CONSTRAINT: preserve complete old per-node display state, then reconcile locally against current state.

NON-DESIRED: leaf-only/live maps; replace old state before clearing; redraw root; clear a sibling's new pixels; refresh only the new rectangle and leave ghosts.

Distinct likely branches: missing internal nodes; hidden/removed child ghosts; movement clearing sibling pixels; whole-root redraw; segment/style/control loss. No internal representation is pinned. Probe Step 2 through continued agent sessions, never independently cold.

Full evidence: `/tmp/rich-lane-i-20261004-zCfBiS/REPORT.md`.

Rating: P1 4, P2 2, P3 2, P4 3, P5 4, P6 3, P7 3 = **21/28 MEASURE**.
