# GENESIS-ELF-001 — manual offline guest gate

**Status:** Proposed integrated candidate on `flight/003-elf-triad-candidate`. Contract tests and host-run deterministic carrier demo can be run in CI. **An ISO build, VM boot, guest execution, installed persistence, and live OpenManus provider conformance remain unverified** until independently observed.

This is a cross-repository composition of [STATIC OS GENESIS-001](GENESIS-001.md), [Workbench ELF carrier prototype PR #60](https://github.com/the-static-collective/static-workbench/pull/60), and the still-draft [LOADOUT OpenManus PR #18](https://github.com/the-static-collective/LOADOUT/pull/18). The image manifest pins exact Workbench commit `f0ee71a5a6941d2efdc36d48f0a06a7f39472884` from the **draft** carrier PR, not an approved or merged release. The change is proposed in a child STATIC OS branch; no production/static-os main source pin is changed by this PR.

## Why this cross-smash

GENESIS-001 already installs the manifest-pinned Workbench into `/opt/static-os/workbench-venv`. This slice adds no separate agent framework, model dependency, boot-time service, installation privilege, or wider filesystem access. The same pinned Workbench source contains `static_workbench.elf_genesis`; the ISO candidate installs a *manual* command `static-elf-proof`. Its chroot hook refuses a pinned source lacking that module. The manifest's `elf` record ties the guest fixture to the **same exact source commit** as HOUSE. The guest command refuses if its embedded manifest and installed source record disagree.

The experimental carrier is a *deterministic fixture*, not a live agent. It instantiates a first unique occurrence from a digest-pinned seed, verifies a deterministic artifact and unadmitted receipt, then creates a distinct successor workspace from the first artifact with an explicit parent-receipt digest. The second output is also verified. The fixture runs in an ephemeral temporary directory; this proves neither a persistent Vault nor transport between machines.

## Current contract gate (CI / build VM)

```sh
python3 scripts/validate-manifest.py manifest/genesis-001.json
python3 -m unittest discover -s tests -v
sh -n config/includes.chroot/usr/local/bin/static-elf-proof
```

The STATIC OS GitHub workflow also fetches the exact pinned Workbench commit and runs the deterministic ELF demo using the source checkout. That is a **host-run integration smoke**: it does not prove that the live image was built, booted or ran offline.

## Guest gate, after independent ISO/VM boot proof

Build the candidate only in a disposable Debian bookworm amd64 VM, using [GENESIS-001](GENESIS-001.md). Boot the resulting ISO in an isolated VM. Disconnect the guest's network adapter before the following checks. As the ordinary live user, *not root*:

```sh
cat /usr/share/static-os/house-source-commit
systemctl --user status static-workbench.service
curl --noproxy '*' http://127.0.0.1:13700/
static-elf-proof
```

`static-elf-proof` verifies the embedded manifest, declared exact source commit, presence of the ELF module, and manual-only fixture declaration before running the two-occurrence demo from the installed Workbench Python venv. Capture its JSON stdout, guest clock, image SHA-256, network-disabled observation, and VM/firmware details **outside the disposable guest**. An external observer must check the record; self-reported output alone does not prove guest isolation or offline state.

Expected demo fields include `first_verified=true`, `second_verified=true`, `distinct_occurrences=true`, `provider=deterministic_fixture_not_openmanus`, `live_provider_conformance=NOT_RUN`, and `os_image_boot=NOT_RUN`. The last field means the *demo itself* does not establish a boot claim; separately witnessed successful guest boot is the necessary OS evidence.

The live ISO has no persistent installed data store. Rebooting it destroys the fixture's temporary workspaces; **do not claim cross-boot continuity** from this gate. A later slice must supply a separately admitted, explicitly provisioned persistent seed carrier and prove restore/re-hatch after a cold boot.

## Separate, unearned gates

* **OpenManus:** The exact-pinned provider still requires an actual live occurrence through the existing LOADOUT #18 effect membrane and independent STATIC-NODE delta verification. Neither ELF test nor successful VM boot proves live provider conformance.
* **Persistence:** An immutable Ark/seed must be deliberately stored outside the disposable guest; another boot receives bytes and lineage, not credentials, authority, or identity. Defer to an explicitly designed persistence gate.
* **System evolution:** A candidate capability may be built and verified in an isolated child, but incorporation into the image requires independent acceptance, explicit human approval, and rollback. The guest ELF command has **no** upgrade, OS write, launch-on-boot, root, merge, publication, or promotion rights.

## FLIGHT-003 source reconciliation

This branch pins combined Workbench composition+ELF draft PR #62 at the exact SHA above. The original standalone ELF implementation and tests originated in Workbench #60; the additional composition code is experimental Workbench #48/#57/#61 ancestry. The static contract and host-only ELF proof must be rerun on this exact combined source. Passing the host-only smoke never proves ISO boot, source-run equivalence for all new Workbench modules, real user persistence, or guest integration of TranchNode/Storyship/Corpus/Jubilee.
