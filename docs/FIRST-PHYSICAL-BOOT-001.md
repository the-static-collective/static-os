# FIRST-PHYSICAL-BOOT-001 — cold USB witness gate

Status: executable physical-proof candidate, stacked on `GHOT-IDLE-OPERATOR-001`.

This slice exists for one purpose: turn the existing GENESIS live-image candidate into a bounded, attributable claim that a real powered-off machine booted STATIC OS from removable media and reached HOUSE offline.

It does **not** install STATIC OS, prove persistence across cold boots, authorize any organ, or let CI impersonate a physical witness.

```text
ISO BUILD != BOOT
VM BOOT != HARDWARE BOOT
HARDWARE BOOT != INSTALLED OS
HOUSE OPENED != PERSISTENCE
HUMAN OBSERVATION != CI ASSERTION
```

## 1. Freeze and validate the exact source

Use a disposable Debian bookworm amd64 build VM. Record the exact STATIC OS commit before building.

```sh
git rev-parse HEAD
python3 scripts/validate-manifest.py manifest/genesis-001.json
python3 -m unittest discover -s tests -v
```

The resulting receipt binds both the STATIC OS source commit and the manifest-pinned Workbench commit.

## 2. Build the existing GENESIS ISO

Install the prerequisites listed in [GENESIS-001](GENESIS-001.md), then run:

```sh
sudo ./scripts/build-iso.sh
```

The existing builder leaves one ISO and `image.sha256` under `.build/genesis-001/`. Build success remains only an image claim.

Initialize the physical witness receipt against the exact ISO:

```sh
python3 scripts/physical-boot-receipt.py init \
  --iso .build/genesis-001/<the-built-image>.iso \
  --out first-physical-boot-001.json
```

This command hashes the image and records source identity. It deliberately leaves every observation field unset.

## 3. VM gates first

Before touching removable media, independently observe:

1. BIOS-mode VM boot.
2. UEFI-mode VM boot.
3. Network disconnected.
4. STATIC desktop visible.
5. HOUSE reachable at `http://127.0.0.1:13700/`.

Only after direct observation, set the corresponding `vm` booleans in the receipt to `true`.

A generated ISO or successful host test does not satisfy these fields.

## 4. Write disposable removable media

Use an expendable USB drive and a trusted image writer. Confirm the device by model and capacity before writing. Do not select the machine's internal disk.

No installer is part of this experiment. Do not mount or intentionally write the internal system disk from the live session.

## 5. Cold physical boot

With the target machine powered off:

1. Disconnect wired networking and disable Wi-Fi before the proof.
2. Insert the STATIC OS USB.
3. Use the firmware one-time boot menu to select the removable device.
4. Observe the STATIC desktop.
5. Confirm HOUSE:

```sh
systemctl --user status static-workbench.service
```

Then open:

```text
http://127.0.0.1:13700/
```

The required physical claims are intentionally narrow:

- the machine booted from the USB;
- the desktop became visible;
- HOUSE answered on loopback while disconnected from the network;
- no installer was invoked;
- the operator did not intentionally write internal storage.

## 6. Human observation receipt

After the event, edit `first-physical-boot-001.json`:

- change `receipt_status` from `candidate` to `observed`;
- set only actually observed VM and physical booleans to `true`;
- fill `witness.name`;
- fill `witness.observed_at` as RFC3339 with timezone;
- write a short literal `witness.statement`.

Keep these nonclaims unchanged:

```json
{
  "installed_os": false,
  "persistent_cross_boot": "not_proven"
}
```

Verify:

```sh
python3 scripts/physical-boot-receipt.py verify first-physical-boot-001.json
```

The verifier refuses an agent witness, an incomplete physical gate, an installer claim, or a promotion to installed/persistent OS.

## Acceptance

`FIRST-PHYSICAL-BOOT-001` is earned only when the completed receipt validates and refers to the exact ISO actually booted on physical hardware.

The next experiment may pursue persistent removable state. That is a separate claim.
