# STATIC-CAD-003 — Question-Driven CAD Workbench

Status: **draft, reversible userspace experiment** in Static-OS.
Stack: APPARATUS-COMPILER-002 (#52) → QUESTION-FIRST-SESSION-001 (#51)
→ V1 (#50). All parents are reviewable and not assumed merged.

## Thesis

The missing-instrument question becomes a **source-bound parametric engineering
design**, not just another prose answer.

    APPARATUS-002 typed graph and validated question ancestry
      → CAD parameter sheet with exact units and bounded integers
      → 2D part profiles / through-bores / pitch reference
      → 3D placement / plane mate / conservative AABB interference
      → constraint-report and material-neutral BOM
      → SVG plan/elevation and ASCII DXF R12 plan
      → optional operator-run FreeCAD macro source
      → exact artifact hashes / source design ID / revision ancestry
      → separate engineering review; never auto-fabricate

This is **NOT the entire AutoCAD product**. The first supported mechanism
family is a gear-reference mounting system with two rectangular parts, one
upright through-bore, and four base mounting holes. The CAD core uses exact
integer micrometre dimensions and fixed safe graph shapes. It does not
contain an unconstrained geometry solver, involute gears, true multi-body
kinematics, FEA, CAM, MEP, imported DWG editor, fabrication or motion control.

It is a practical CAD substrate: an executable, extensible document model,
geometry/drawing export and a separately gated path to an existing precise
B-rep CAD engine. It is *not* a replacement for FreeCAD's own geometry engine.

## What is actually compiled

The APPARATUS-002 seed supplies 12:36 gear ratio and screw lead. The
selected apparatus candidate remains explicit: "direct-screw" or
"gear-then-screw". The design sheet supplies a gear module, plate thickness,
walls, bore diameter, four drill-hole diameters, margins, clearances and
material candidate. All dimensions use **µm integers** in authoritative
JSON; exported drawing units are **millimetres**.

The compiler derives a base-plate envelope and bearing-upright envelope
from the *driven gear's reference pitch diameter*, not a physical
involute tooth model. It checks:
- maximum size and allowed ranges; rejects bool/float/string input;
- mount-hole edge clearances and distinct rows/columns;
- bearing bore wall thickness;
- positive placements and contained upright;
- conservative axis-aligned 3D *bounding-box* noninterference;
- one coincident plane mate at base top / upright bottom;
- all parts correspond to a known typed apparatus candidate;
- exact source plan (APPARATUS-002 content-addressed model) and source
  witness remain unchanged; the authentic Leonardo image is *not* present.

Result is a **STATIC_CAD candidate**, not a certified assembly. No
fastener engineering, loads, stiffness, tolerances, material strength,
clearance class, fabrication process, fit, legal reception, thermal stress,
manufacturability or physical motion has been independently assessed.
False positive AABB overlaps may refuse some valid candidate geometries.

## Four useful, actual files plus the project and manifest

The generated package directory contains:

- project.json — full parametric model, exact source ancestry, typed graph,
  constraint flags, part definitions, revision-parent link, SHA-256 address;
- drawing.svg — base top and upright elevation preview with holes and
  explicitly labeled gear pitch reference (not toothed gear geometry);
- plan.dxf — ASCII DXF AC1009 with 2D LINE and CIRCLE entities;
  NOT editable semantic dimensions, fillets or DWG fidelity;
- bill-of-materials.csv — the two part counts, bounding dimensions, hole
  counts and **unverified** material proposal;
- generate-freecad.FCMacro — source code for an **operator-run** FreeCAD
  macro that creates actual B-rep boxes, boolean cylindrical through-holes,
  validates resulting shapes and exact positive-volume interference,
  and asks FreeCAD to export FCStd, STEP and STL;
- manifest.json — exact SHA-256 for each generated file, the parent
  project identity, and explicit status of what has and has not executed.

The CAD generator itself NEVER runs FreeCAD, so **FCStd / STEP / STL are
NOT produced by CI**. If the operator separately runs the macro in a
compatible FreeCAD installation, its results require independent
inspection and validation; simply generating the macro does not prove
the B-rep engine, format exports or actual 3D part correctness.
The macro requires a fresh, nonexistent directory named via
STATIC_CAD_FREECAD_OUTPUT. It refuses overwrite. Its output is a
neutral CAD *candidate*, not a construction ticket.

The FreeCAD FCStd documents contain static PartDesign::Feature B-rep
shapes authored from the source parameters. Native interactive FreeCAD
sketch constraints, feature history, part properties, associative
dimensions, motion joints and undo/redo are future separate work.

## Revisions are immutable, not overwritten

Change the parameter JSON and run a revision against the original
project. The child retains its original source apparatus identity and
records the prior project's content-addressed ID. It cannot silently
switch a question or selected apparatus, and revisions without a
parameter change refuse. The parent package remains independently
verifiable.

A new CAD candidate may be prepared or reviewed even when GHoT does
not have manufacturing hardware. No file/drawing/plan changes owner
permissions or signs an approval. The source-anchored question is
*scientific inspiration*, not evidence the Leonardo folio contains
this precise gear-leadscrew design.

## How to run

Choose a trusted local GHoT checkout with native Instrument Rack;
the CI source is pinned to:

    the-static-collective/GHoT @ 6e4aab6aec3b28f8dd50d01c3d571ae754c653d1

Set a **private GHoT_HOME**, and opt into the 002 simulation-only
instrument pantry. No physical hardware is used:

    export GHOT_SRC=/path/to/trusted/GHoT
    export GHOT_HOME="$HOME/.local/state/static-cad-003/ghot"
    export GHOT_ADAPTER_MANIFESTS="$PWD/integrations/apparatus-002/adapter-manifest.json"

First compile the source apparatus proposal (no execution):

    python3 scripts/apparatus-compiler.py compile \
      --ghot-root "$GHOT_SRC" \
      --seed fixtures/apparatus-002/source-grounded-question.json \
      --out /tmp/cad-apparatus-source.json

Then compile a CAD design package, explicitly choosing one candidate:

    python3 scripts/static-cad.py compile \
      --apparatus-plan /tmp/cad-apparatus-source.json \
      --parameters fixtures/static-cad-003/reference-parameters.json \
      --candidate gear-then-screw \
      --out-dir /tmp/static-cad-design-001

Verify exact source content and generated geometry again from cold files:

    python3 scripts/static-cad.py verify \
      --out-dir /tmp/static-cad-design-001

Edit only the parameter JSON (example: change base_width_um to 68000),
then create a second candidate **without mutating the first**:

    python3 scripts/static-cad.py revise \
      --apparatus-plan /tmp/cad-apparatus-source.json \
      --parameters /tmp/cad-changed-parameters.json \
      --parent-project /tmp/static-cad-design-001/project.json \
      --out-dir /tmp/static-cad-design-002

The DXF and SVG are ready for inspect/review. To generate real B-rep
export candidates, run the FCMacro explicitly in FreeCAD with a fresh
STATIC_CAD_FREECAD_OUTPUT target directory and then independently
review its FCStd / STEP / STL, including units and geometry. This
integration is not executed or certified by hosted CI.

## Hostile proof

    GHOT_SRC=/path/to/pinned/GHoT python3 -m unittest tests.test_static_cad_003 -v

CI also re-runs APPARATUS-COMPILER-002 and QUESTION-FIRST-SESSION-001
against the pinned native signed GHoT source and uploads the inert CAD
design package as a GitHub Actions artifact.

Among the adversarial cases:
- wrong/missing parent plan ID and unverified selected candidate;
- injected dynamic expressions, shell commands, floats, booleans,
  negative dimensions, or material authority;
- inadequate hole edge clearance, wall or available layout area;
- model mutation/reforged project IDs, unearned source bytes, changed
  drawing and intentionally rehashed drawing;
- revising a design without a change or switching question implicitly;
- output directory existing, sensitive files receiving 0600 mode;
- preview DXF lines/circles, source-checked FreeCAD macro,
  exact BOM hashes and cold-reproducible package integrity;
- **zero GHoT instrument execution** during CAD compilation/verification.

## The real roadmap: breadth without false authority

003 establishes the *kernel/contract*: immutable parametric document,
bounded profile/body topology, validated assembly transforms,
projection and neutral export paths. Future bounded organs:

- **004 Sketch & Constraints**: parametric 2D lines/arcs/circles,
  point-on-line, tangency, dimension equality, under/overconstraint,
  explicit solver residuals and verified geometric kernels.
- **005 Features & Solids**: expressive sketch-pad/pocket/revolve,
  boolean feature DAG, native FreeCAD/OCCT B-rep verification,
  precise STEP, STL and CAD-native editable history.
- **006 Assembly & Motion**: typed mechanical joints,
  gear/screw kinematics, collision sweeps, tolerance stack-up,
  static/dynamic load-envelope checks with real measured inputs.
- **007 Source Through Design**: LemonPRESS-driven exact
  folio/source-page attribution, translations, inferred geometry
  distinctions and source/derived artifact ancestry.
- **008 Manufacturing Gate**: drawings, BOM, material properties,
  toolpath simulation and independent human/reviewer/operator
  permission *before* any physical effect; separate fabrication
  hardware controller. No inferred construction authorization.

## Laws

    QUESTION != FABRICATION ORDER
    HISTORICAL SKETCH != VERIFIED MODERN CAD
    GEAR PITCH CIRCLE != TOOTH GEOMETRY
    DESIGN PARAMETER != PHYSICAL CALIBRATION
    DXF PROJECTION != FULL 3D CAD
    FREECAD MACRO GENERATED != BREP EXECUTED
    STL EXPORTED != PRINTED
    PARTS TOUCHING != LOAD-BEARING JOINT PROVEN
    MATERIAL LABEL != STRUCTURAL PROPERTIES
    PARTIAL AABB CHECK != COLLISION-FREE MOTION
    DESIGN HASH != SIGNED HUMAN APPROVAL
    CAD REVIEW != PHYSICAL SAFETY AUTHORITY
    INSTRUMENT GAP != AUTOMATIC TOOL PURCHASE
    MODEL != REALITY
