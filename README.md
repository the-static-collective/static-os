# STATIC OS

A project-owned, Linux-based computational habitat for the Static Collective.

**Status:** GENESIS 001 / bootstrap under review. This repository does not yet contain a verified bootable ISO or installed OS.

The distribution integrates independently governed organs without absorbing their identity or authority. Debian supplies the kernel, boot, packages, and hardware support; STATIC OS owns its image composition, HOUSE session entry, provenance manifest, test gates, and operator documentation.

**Non-collapses:** installed != ready; discovered != authorized; build receipt != boot proof; image != installed persistence; candidate != admitted; source SHA != reproducible package closure.

See the GENESIS-001 proposal branch and PR for the executable first slice. Until its image and boot gates are run, claims of a working STATIC OS are premature.

## Workbench desktop installer preview

[LAUNCHPAD-002](docs/LAUNCHPAD-002.md) packages the pinned Workbench with its own
Python runtime for Zorin 17+/Ubuntu 22.04+ amd64. The **Desktop installer preview**
workflow produces a native `.deb`: install it through Software Install, then
open **Static Workbench** from the application menu. See the linked document for
build status boundaries, compatibility, logs and removal behavior.


## STATIC 2012 reference-machine experiment

[STATIC-2012-001](docs/STATIC-2012-001.md) defines a deliberately low-end
reference target: 2-core amd64, ~4 GiB RAM floor, no required GPU, and
network-optional continuity after initial sync. It classifies capabilities as
GREEN local core, YELLOW degraded local, BLUE dispatchable, or RED deliberately
unavailable. Any non-GREEN capability must name its resource bottleneck and a
lawful fallback.

The self-audit and clone planner are contract tools only. They do not claim a
physical 2012 machine has been tested and do not automatically clone or execute
external projects.
