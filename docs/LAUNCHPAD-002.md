# LAUNCHPAD-002 — desktop installer preview

A native Debian package for Zorin 17+/Ubuntu 22.04+ on amd64. This installs
Workbench as an application on the existing OS. It does not install STATIC OS.
Older Zorin versions are not yet supported; do not promise compatibility based
only on the bundled Python runtime (the host C library still matters).

## Human path

1. Download `static-workbench-desktop_amd64.deb` from a successful **Desktop
   installer preview** Actions run (unzip the artifact download first).
2. Open the package with the system's Software Install application and choose
   Install. The system may request the administrator password and download
   distro dependencies. No terminal or host Python upgrade is required.
3. Choose **Static Workbench** from the applications menu. HOUSE opens in your
   default browser after its server starts. Subsequent clicks reopen the desk.

The server remains running after closing the browser, until logout. There is
no login autostart. Remove the application using the system package manager;
log out before removal or upgrade to stop the running process. Configuration,
project files and the user journal are not removed by uninstalling.

## Build and authority

`bash scripts/build-desktop-deb.sh` on an Ubuntu 22.04 amd64 builder with Python
3.11+, venv, git and dpkg-deb. CI uses that baseline, installs build dependencies
only on the builder, freezes the exact manifest-pinned HOUSE source with its
Python runtime, constructs the app using the frozen executable, and emits a
`.deb` plus SHA-256 checksum. There are no package maintainer scripts, download
hooks, pip calls or source checkouts on the receiving computer. The package
manager owns `/opt/static-workbench` and desktop integration; HOUSE runs as the
ordinary logged-in user and retains its loopback/configuration boundaries.

Existing `~/.config/static-workbench/config.toml` is read unchanged. Without
one, HOUSE defaults apply, including the `~/static` project root. Logs are at
`~/.local/state/static-workbench-desktop/server.log`. A pre-existing separately
started HOUSE using the same port causes a visible error, not a kill or takeover.

The source SHA and resolved dependency list are included in `/opt/static-workbench`.
Dependencies are resolved at build time, so this is not yet a reproducible or
signed release. Artifact checksums detect file changes, not publisher identity.
Build success is not evidence of GUI install on the user's Zorin machine.
A signed public release and real Zorin desktop install/launch/uninstall test
remain release gates. No ISO/ELF/boot gate is advanced by this application package.
