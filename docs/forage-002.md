# FORAGE-002 — WALL-E Field Scout

**A little mobile eye for a permission-first workshop.**

The point is not to build a robot that takes anything it sees. It's to build a
scout that notices something, asks where it came from, proposes how it *might*
be useful, and can hold indefinitely while the right person checks the
ownership, habitat, hazards and actual pickup terms.

This is a **standalone static phone-friendly browser page plus native Python
importer**. It is *not yet deployed to Static Live or an installed Android
app*. It does not turn on cameras automatically or use a camera without the
user selecting a photo. It uses the mobile browser's device camera/file picker
on devices that support `capture=environment`.

Parent: [FORAGE-001](forage-001.md). This experiment is stacked on the
**FORAGE-001 permission/custody draft**. Robot Garden, GHoT, reLATTE and Jubilee
remain separate authorities.

## Operational sequence

```
USER — notices offered or abandoned-looking thing
  |
  v
PHONE — chooses/captures a local JPEG or PNG
  |
  +--> Human selects category, property/source class, site, steward,
  |    purpose, visible concerns and uncertain observations
  |
  +--> Original image bytes hashed locally (not uploaded)
  |
  v
FORAGE-002 — exact FORAGE-001 lead + separate image evidence JSON
  |
  v
FORAGE-001 — cold replay, authority HOLD, human review required
  |
  +--> Deterministic possible-use labels (NOT live GHoT model inference)
  |
  v
HUMAN — seeks genuine owner/land manager permission
  |
  v
FUTURE reLATTE owner-local transfer / physical inspection
  |
  v
FUTURE Robot Garden tests and Jubilee inventory ONLY IF admitted
```

### First mobile experience

1. Serve `forage/mobile/` from an **HTTPS static host** with a secure context.
   Example after a deliberate deployment to a GitHub Pages/Static Live project:
   `https://YOUR-STATIC-HOST/index.html`. No URL is live merely because
   these files exist in GitHub.
2. Open the site on a phone. Choose **Take photo** or a local existing image;
   on mobile browsers this may open the camera or the photo picker.
   Supported formats: JPEG and PNG, up to 16 MiB. HEIC and raw video are not
   supported here.
3. Enter your own observation and tentative category. Choose the source
   jurisdiction and land class; unknown/default choices are allowed and **held**.
   Unknown owner or unknown location can use the safe placeholder references
   `unknown:steward` and `unknown:site`; neither is a real authorization.
4. Select any *known* hazard flags. Not selecting a hazard does **not** establish
   hazard absence or physical safety.
5. Tap **Compile HOLD encounter**, then download both JSON files. Save the
   original photo too. The page never sends image bytes, geolocation, EXIF or
   personal info to a server; hosted static page resources will still be loaded
   from whatever HTTPS host you choose.
6. On a machine holding the same **unchanged photo file** and the files from
   the phone, run the source-verifying CLI:

```bash
python3 scripts/static-forage-scout.py receive \
  --lead /path/to/forage-lead-XXXX.json \
  --photo-evidence /path/to/forage-photo-evidence-XXXX.json \
  --photo /path/to/unchanged-phone-original.jpg \
  --out dist/scout-observation-002.json

python3 scripts/static-forage-scout.py verify \
  --lead /path/to/forage-lead-XXXX.json \
  --photo-evidence /path/to/forage-photo-evidence-XXXX.json \
  --photo /path/to/unchanged-phone-original.jpg \
  --out dist/scout-observation-002.json
```

The resulting `static-os.forage-scout/v0` binds the exact file hash, operator-
entered FORAGE-001 lead, original unreviewed assessment and category-selected
possible-use hypotheses. It does **not** inspect a JPEG's pixels for actual
motor/plant/rock identification, prove EXIF truth, sign a photo at capture, or
verify entry/removal authority. The Python importer checks magic signatures
and bytes, not full image decoding; malformed content with a valid header is
not proof of a real picture.

For local development on a desktop (browser served at secure-context
`localhost`), run:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory forage/mobile
# Open http://localhost:8765/ on the *same* machine.
```

To use it on the phone from a remote host or another LAN device, use HTTPS;
plain `http://<LAN-IP>` usually won't provide WebCrypto secure context and
photo hashing will refuse to proceed. Do not interpret the GitHub code view as
a deployed app.

## How the suggestions work

`forage/mobile/scout-core.mjs` and `forage/scout.py` hold the same short,
static list of **category hypotheses**. Selecting `TECH_PARTS` may suggest
a bracket or fixture, motor research, and a fastener recovery check. A photo
is **not** parsed by any image recognition model, a live GHoT instrument is
**not** called and nothing is classified independently. Even a human's correct
identification says nothing about owner permission or electrical safety.

### Credible next upgrades

1. **Physical image inspection:** reuse Robot Garden's original-JPEG
   provenance and controlled T3i/GoPro visual witnesses; keep names/lens
   calibration and time unverified until proven.
2. **Actual GHoT perception:** add an explicit, opt-in classification donor
   with model provenance, confidence, contradictory candidate lists, training
   limitations and the permanent right to HOLD.
3. **Permission:** a reviewed source-specific legal evidence/owner action
   crossing from FORAGE-001, not a screen trick.
4. **Physical WALL-E:** a separately authenticated robot organ capable of
   inspection, then later supervised gripping and sorting. No remote
   motion, lock bypass, picking or transport permissions exist here.
5. **Intake/repair:** workshop observation → source verification →
   quarantine → safety evaluation → human-local decision → signed receipt →
   possible approved physical inventory.

**Invariants:** SEE != TAKE; DISCOVERY != OWNERSHIP;
CAMERA FILE != AUTHENTICATED CAPTURE; POTENTIAL USE != VERIFIED PART;
NO HAZARD SELECTED != SAFE; CATEGORY MENU != GHoT INFERENCE;
PICKUP PROPOSAL != MACHINE MOTION; HASH != SIGNATURE;
SOURCE ADMITTED != PHYSICAL INVENTORY.
