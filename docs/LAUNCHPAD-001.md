# LAUNCHPAD-001 — local self-start, independently gated next flights

**Status:** draft, user-invoked bootstrap from the STATIC OS Flight-003 candidate.
This starts exact-manifest-pinned Workbench, not a live OS image.

From an ordinary Zorin/Linux terminal in the STATIC OS launchpad branch:

- bash ./scripts/start-train.sh --check : read-only prerequisites/source/config report.
- bash ./scripts/start-train.sh --start : explicitly clone (or verify an existing
  exact checkout), create a user-owned venv, install exact pinned Workbench
  source into it, create local config only if absent, and start HOUSE in the
  foreground at its configured loopback URL.

The command intentionally does not require root, format a disk, launch a VM,
install host packages, change an existing config, reset a local checkout,
enable an auto-start service or mutate the host OS installation.

The operator is still authorizing dependency installation and execution of
the pinned Workbench source as their Linux user. This is not an untrusted-code
sandbox. Existing config may point to other roots; edit it deliberately if
the new checkout is not visible. An existing service on the configured port
may prevent launch.

The STATIC OS live image still requires a separate disposable Debian
Bookworm build VM and independently observed BIOS/UEFI, offline HOUSE,
manual ELF, state/restart, recovery and cross-boot Storyship gates.
The in-HOUSE Launchpad page shows these as unverified unless separately
witnessed, never inferred from local files or successful source tests.
