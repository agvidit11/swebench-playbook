# commons-geometry-transforming-facet-import

- Date/machine: 2026-10-05 / devvm23237
- Repo/base: `apache/commons-geometry` @ `3f268c968779c4f3105c870e32b6d41f94abd5d1`
- Seam: facet transform -> transforming reader view -> transform-before-weld triangle-mesh import
- Trap: natural order irreversibly welds vertices and reflection preserves stale winding
- Routing: `MEASURE`, three fresh-session K-to-N steps
- A4: `CLEAR`; no Commons Geometry or exact-symbol peer found

## User problem and base evidence

My CAD facets use model coordinates. Scaling after import merges nearby vertices too early, and mirrored axes turn closed solids inside-out. I need to transform geometry while reading it, before precision-based vertex welding and mesh construction.

With epsilon `0.1`, two parallel facets at x=0 and x=0.01, then scale-x 100, current read-then-transform produces only three vertices with bounds still at x=0; transform-before-weld produces six vertices spanning x=0..1. Reflecting a unit cube makes its center classify OUTSIDE and an exterior point INSIDE, with infinite size. OBJ, STL, and TXT export/reimport retain that wrong classification because vertices change but face order does not.

## Steps

1. Transform one `FacetDefinition`, preserving absent normals and keeping supplied normals consistent with transformed winding under translation, non-uniform scaling, and reflection.
2. Add a transforming `FacetDefinitionReader` view consuming Step 1 while preserving facet order, EOF behavior, and close delegation.
3. Add transformed `BoundaryIOManager3D.readTriangleMesh(...)` behavior consuming Step 2 so transforms occur before polygon conversion and precision-based vertex welding.

CONSTRAINT: transform facet geometry and orientation before any lossy polygon conversion or vertex welding.

NON-DESIRED: read then transform; transform vertices without correcting winding/normals; invent normals when absent; close or reorder the wrapped reader incorrectly; weld in source coordinates; fix only exported output.

Independent branches include translation, non-uniform scale normals, one- versus two-axis reflection orientation, nullable normals, lifecycle delegation, vertex-weld order, closed-region classification, and export/reimport persistence. Step 3 is distinct mesh materialization consuming Step 2's artifact. No single-turn fallback.

Existing authorities: `Transform.preservesOrientation()`, `FacetDefinitions.toPolygon(...)`, and `SimpleTriangleMesh.Builder.useVertex(...)`.

Evidence: `/root/scout_commons_geometry` handoff.

Rating: P1 4, P2 3, P3 4, P4 4, P5 3, P6 3, P7 3 = **24/28 MEASURE**.
