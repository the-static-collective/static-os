# GENESIS BOOT 004/005 — two non-Debian environments, one independent source history

**Scope:** the original working CANNON first-boot runner and its open-PR donors can run in Alpine Linux (musl), Fedora Linux (RPM), and—separately—the proposed Alpine Live USB/ISO. These are distinct outputs. An OCI image is a Linux userland, **not** a USB-bootable operating system; a generated ISO is not a demonstrated boot until a separate QEMU/physical boot gate succeeds.

## Proven baseline: Alpine + Fedora OCI native runtimes (BOOT 004)

- Source: [STATIC OS PR #93](https://github.com/the-static-collective/static-os/pull/93).
- Verified hosted run: [Alpine and Fedora native execution](https://github.com/the-static-collective/static-os/actions/runs/40880951037).
- Sources: **11 immutable Git commit checkouts**, independently supplied from CANNON (two distinct commits), STATIC OS, webZ, GrO, GHoT (two commits), JAR;VIS, Full Measure, Band Runtime and BananaSpork. The exact version of each source is in `manifest/genesis-boot-003.json`; none has to be merged to main.
- Builder: Alpine `node:24-alpine`; Fedora `fedora:43` + upstream Fedora Node24 packages. Each image contains original Git objects, Python 3, a Node24 runtime and the existing Garden TypeScript package closure.
- Runtime test: complete original `boot-console-native.test.mjs` using a **non-root user in a network-disabled, read-only container** with local temporary state. It actually executes the House A/B first-boot composition, source-integrity checks and original Warm Thread crossing, restarts the local server, detects tampering, restores and cold verifies. Two different fictional house surveys; zero physical measurements, zero independent real operators.
- Workflow uploads actual **loadable OCI archives** `oci-image.tar.gz` and `oci-image.tar.gz.sha256` plus generated proof receipts and locally rendered HTML; they have a finite GitHub artifact retention. Image bases are selected by *tags*, not content-addressed base digests, so builds are currently **not bit-identically reproducible** or qualified for unrelated production workloads.

### Running the OCI images

For local source testing on a trusted Linux host:

```sh
# From GitHub Actions, download the desired image artifact and verify its SHA.
sha256sum -c oci-image.tar.gz.sha256
gzip -dc oci-image.tar.gz | docker load

# Smoke-test original userland code without any network access:
docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges \
  static-genesis-boot-004:alpine test-native

# On a trusted **Linux** machine only, use host networking to access
# the *loopback-bound* user interface from the host browser:
docker run --rm --network host static-genesis-boot-004:alpine
# Then open http://127.0.0.1:8766/ in the local host browser.
```

The standalone `test-native` command creates transient internal outputs; for persisted, independently inspectable receipts mount a writable local directory as `/home/genesis/.local/state/static-genesis/runs` owned by UID 10001. **Do not use host networking on untrusted machines or use these experiments with sensitive personal/household data.** The real app has no auto-run BUILD/WARM action and doesn't listen on public interfaces, but original experimental Git code is not a verified secure server.

## Alpine Live ISO candidate (BOOT 005)

This experiment uses *Alpine's own* `aports/scripts/mkimage.sh` and `apkovl` mechanism, not Debian live-build. A custom Alpine profile includes Node24, Python3, Git, local OpenRC boot scripts, the **full 11-original-source offline payload** and the first-boot server, with source-owned `.git` histories still present. The expected output is a diskless x86_64 Alpine Live `.iso` with BIOS/UEFI boot metadata. It is not an installer and it never writes to host storage.

During build, an ephemeral `abuild` signing key signs the *image's local APK index*, not user identities or organizational permissions. Alpine packages come from the official v3.23 main/community repos and the upstream stable branch of `aports`. They are not all version/digest pinned yet, and must be reviewed for distribution rights and reproducibility before physical deployment.

A normal diskless boot starts a **nonroot, loopback-only** local first-boot server in OpenRC. The user can interact on the same machine with the existing JS browser interface if a browser/GUI is provided externally; this first Alpine profile is *console-oriented*, so it does **not** claim an automatically opened graphical browser. The first greeting appears in the boot terminal/MOTD. The only automatic behavior is local service startup—not source-native project execution. Actual BUILD and WARM require separate explicit requests.

### Independent Alpine ISO CI probe

The [BOOT 005 workflow](https://github.com/the-static-collective/static-os/actions/workflows/genesis-boot-005-alpine-live.yml) stages the same exact open-PR source trees via a known-working Alpine OCI build, assembles a real ISO using Alpine's native tooling, then attempts to boot **that ISO** with QEMU BIOS and **network disabled**. The special **CI-only** image adds a local software probe that deliberately triggers a fictional House A/B run and fictional Warm Thread, cold-verifies both, and writes serial proof markers. This probe is not included in the normal user-facing ISO recipe.

A valid success requires all of: an actual single ISO and SHA256; QEMU BIOS kernel-to-userspace boot; live local server started; original House A/B native execution plus independent cold replay; original Warm Thread execution plus independent cold replay. An image merely saved to disk or bootloader appearing onscreen is not sufficient.

**Unverified until independently measured:** ISO BIOS/UEFI guest boot, a GUI login, disconnected physical hardware compatibility, correct USB imaging procedure, reliable source package provenance, application updates, installed persistent state across reboots, live original reLATTE exchange, physical sensors, or authorized institutional action. The baseline Alpine and Fedora OCI source tests above remain separately proven even if the Alpine ISO build encounters an upstream `mkimage` problem.

## Shared design law

**The suitcase's first act is to ask what a person wants to build—not to build something without them.** Its non-Debian forms reuse the same independently evolving source-owned code without selecting `main` as universal authority. A successful source test never converts synthetic witnesses or fictional resources into real community facts.
