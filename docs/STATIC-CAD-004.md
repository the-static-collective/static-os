# STATIC-CAD-004 — The Universal Sketch, First Bounded Body

Status: Draft userspace experiment stacked on STATIC-CAD-003 (#53), APPARATUS-COMPILER-002 (#52), QUESTION-FIRST-SESSION-001 (#51) and Static-OS V1 (#50).

## What executes

An exact, bounded 2D sketch language now contains 3–20 named points, a CCW closed contour of line and circular arc edges, up to eight circular holes, constrained integer-micrometre dimensions, and pad/pocket feature intent.

A bounded numerical solver supports: fix point, horizontal, vertical, distance, coincident, equal length, tangent between line and arc, and point on circle. Its damped least-squares iterations and finite-difference Jacobian produce an explicit constraint report: SOLVED, UNDERCONSTRAINED, REDUNDANT_CONSTRAINTS, or INCONSISTENT. Only SOLVED earns geometry exports.

Checks reject non-closed topology, invalid arc radius/sweep, non-positive area, sampled self-intersections, holes outside profile, insufficient edge clearance, overlapping bores, invalid numeric types, extra commands, forged source ancestry, and unsupported features. Geometry validity is a limited sampled software check, not B-rep, tolerance, or professional engineering certification.

## Actual artifacts

- sketch.json — exact source seed and solver outcome bound to its CAD parent
- drawing.svg — lines, circular arcs, two mounting bores and visible label
- geometry.dxf — 2D DXF R12 lines, arcs and circles
- features.json — bounded pad and through-pocket feature plan
- generate-sketch-freecad.FCMacro — operator-run FreeCAD candidate
- manifest.json — exact content SHA-256s and source addresses

The macro, IF separately run by an operator in a compatible FreeCAD installation, builds a Part.Wire from actual line and arc edges, constructs a Part.Face, extrudes the pad, cuts cylindrical through-pockets, checks shape validity, and requests FCStd, STEP and STL exports to a fresh directory. Hosted CI only generates macro source, not actual B-rep geometry.

The source parent is a real STATIC-CAD-003 model, which retains APPARATUS-002 and the existing catalog-level Leonardo conceptual reference. No source folio geometry has been copied or verified. This is a modern design interpretation, not an authenticated Leonardo reconstruction.

## CLI

Use the prior apparatus and Static-CAD-003 instructions to produce a source project from GHoT's opted-in simulation instrument pantry. Copy the exact CAD project_id into a local copy of fixtures/static-cad-004/rounded-mount-sketch.json at cad_parent_id; the checked-in fixture intentionally contains a placeholder so no lineage is fabricated.

    python3 scripts/static-sketch.py solve --seed /tmp/sketch004-seed.json --parent-project /tmp/sketch004-parent/project.json --out-dir /tmp/sketch004-result

    python3 scripts/static-sketch.py verify --out-dir /tmp/sketch004-result

For full reproducible source-to-sketch setup see the dedicated CI workflow at .github/workflows/static-cad-004.yml. That workflow creates a new parent through native GHoT discovery, recompiles a STATIC-CAD-003 project, binds the exact ID into the fixture in its local test workspace, solves the sketch, cold-verifies exact bytes and uploads the design candidate.

CI runs the 004 hostile suite plus inherited 003, 002 and 001 regressions against pinned GHoT source 6e4aab6aec3b28f8dd50d01c3d571ae754c653d1. No RF, manufacturing, network command, motor, boot or human-signature proof.

## Scope and limitations

This is not yet an AutoCAD replacement. It lacks arbitrary unconstrained geometry, robust industrial geometric kernels, semantic DWG editing, native FreeCAD Sketcher dimensions, 3D topological naming, tolerances, collision sweeps, FEA, CAM or CNC/3D printer control. Finite-difference rank diagnostics are provisional numerical statements, not guarantees of engineering degrees of freedom.

No generated sketch has physical execution authority; a FreeCAD macro is inert until independently and deliberately run.

QUESTION != COMMAND
SKETCH SOLVED != FABRICATION APPROVED
NUMERIC JACOBIAN RANK != CERTIFIED DESIGN
DRAWING ARC != VERIFIED BREP CURVE
FREECAD MACRO != FREECAD EXECUTION
DXF != INDUSTRIAL CAD VALIDATION
HISTORICAL CATALOG != VERIFIED GEOMETRY
NEXT QUESTION != NEXT TURN
