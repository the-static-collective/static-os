# STATIC OS

A project-owned, Linux-based computational habitat for the Static Collective.

**Status:** GENESIS 001 / bootstrap under review. This repository does not yet contain a verified bootable ISO or installed OS.

The distribution integrates independently governed organs without absorbing their identity or authority. Debian supplies the kernel, boot, packages, and hardware support; STATIC OS owns its image composition, HOUSE session entry, provenance manifest, test gates, and operator documentation.

**Non-collapses:** installed != ready; discovered != authorized; build receipt != boot proof; image != installed persistence; candidate != admitted; source SHA != reproducible package closure.

See the GENESIS-001 proposal branch and PR for the executable first slice. Until its image and boot gates are run, claims of a working STATIC OS are premature.

## HOUSE-SEED-001: the Suitcase grows a cooperative house

The [Living House generator](docs/HOUSE-SEED-001.md) takes a site/parts survey and creates a deterministic, cold-verifiable, **HOLD-only** staged plan for a one-house model of a cooperative city. It does not install Linux, modify a house, activate sensors, or establish an organization.

```sh
python3 scripts/suitcase.py house-template > site.json
python3 scripts/suitcase.py house-compose --site site.json --profile foundry --media grow > living-house.json
python3 scripts/suitcase.py house-verify living-house.json
python3 scripts/suitcase.py house-render living-house.json > living-house-work-cards.html
```

The existing Suitcase Genesis code and its physical FIRST SIGNAL bench remain independent experimental gates.
