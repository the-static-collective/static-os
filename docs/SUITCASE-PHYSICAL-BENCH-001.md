# SUITCASE PHYSICAL BENCH 001 — first table, first signal

**Status:** preparation and executable inert HTTP experiment. No user hardware has been inspected, soldered, flashed, booted or connected; no live reLATTE federation, private communications, installed OS or public service exists.

## Goal

Get one reclaimed computer to show a fixed local page on a phone **without internet**. Do not start with disk installation, radio transmission, a custom battery pack, real people's records, or soldering.

## What to put on the table

- **WORKSTATION:** working Linux computer with Python 3 (can be BOX-A).
- **BOX-A:** spare x86-64 laptop/desktop and safe original power supply.
- **PHONE-A:** browser-equipped Android/iOS phone.
- **ROUTER-A:** spare Wi-Fi router with WAN cable physically disconnected; avoid client-isolating guest Wi-Fi.
- **USB-A:** spare expendable USB drive, preferably 16+ GB, for a later live-USB boot.
- **RADIO-A / TOOLS:** identify the equipment but leave the radios and soldering iron off.

Fill `field/device-inventory-template.csv` offline using labels, without serials, MACs or identifying data.

## Step 1 — mission plan without any installation

From the extracted source directory:

~~~sh
python3 -m unittest discover -s tests -v
python3 scripts/suitcase.py probe
python3 scripts/suitcase.py compose --profile church --media forest --privacy invitation-only > church-plan.json
python3 scripts/suitcase.py verify church-plan.json
~~~

Candidate must say `HOLD_FOR_BUILD_AND_HUMAN_REVIEW`, with all hardware effects false. Probe only observes the *current* Python host; reported workspace space is not free installation space on another target. The plan digest is not a signature.

## Step 2 — first offline local signal

For loopback: run `python3 scripts/bench-web.py`, open `http://127.0.0.1:8765/` on the same computer, and Ctrl+C to stop.

For a second-device test:

1. Connect computer and phone to the same trusted Wi-Fi router **without any WAN/internet uplink**.
2. Run `ip -4 addr` on Linux and identify the computer's actual private IPv4, for example `192.168.1.20`.
3. Run `python3 scripts/bench-web.py --bind 192.168.1.20 --permit-lan-test`, substituting that computer's real address. Wildcard and public binds are refused.
4. In the phone browser open `http://192.168.1.20:8765/`, using the same actual address.
5. Observe **The suitcase can speak locally.** Record success/failure/date/device labels on `field/first-signal-observation-template.md`. Stop with Ctrl+C.

The page uses **unencrypted unauthenticated HTTP** and carries only fixed, public-safe demo text. Never enter personal, survivor, church-member, legal, medical or child records. The demonstration proves neither cryptography nor reLATTE crossing, discovery, identity, persistence or service delivery. Host/router software may have independent logs. If firewall rules prevent access, do not broadly disable firewall protections.

## Step 3 — live OS trial, separately gated

Get **official Debian Live Xfce amd64** from https://www.debian.org/CD/live/ and use Debian authenticity/USB instructions at https://www.debian.org/CD/faq/. Flashing an ISO **erases the selected USB completely**; identify the spare drive before writing. Boot the spare PC in **Live** mode, never Install, and do not modify internal disks.

Record BIOS/UEFI, input, display and networking observations. Ordinary live media do not prove cross-reboot persistence. The project's `genesis-001-live-iso` candidate is a *different* unverified Debian bookworm build recipe with installer disabled; it first needs disposable Debian VM build, independent BIOS/UEFI VM boot, offline HOUSE and recovery gates. Do not imply it is ready to flash.

## Safety

- No soldering, battery repackaging or mains-power modification now; avoid unknown chargers, loose/damaged lithium cells and unverified voltage/polarity.
- No radio transmission until the exact hardware, permitted frequencies, antennas and regulatory constraints are assessed.
- Do not root or flash a daily Android phone, erase a computer or disable disk encryption.
- Preserve the user's existing personal data and power down unusual hardware safely.

**Claim earned by successful field observation:** one phone loaded one fixed HTTP page from a computer on a disconnected local LAN. Nothing more.

**Evidence ladder:** mission plan → loopback page → disconnected-LAN phone page → official Debian Live boot → custom ISO VM boot → custom physical boot → independently signed two-node reLATTE crossing → consented TABLELIGHT handoff.
