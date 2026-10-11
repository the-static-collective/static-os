# BANDCAMP × FIELD-SCORE-001 — The Singing Sigil

**State:** F0 synthetic adapter + hostile fixture, not an actual QR scan, encoded track,
listener session, Bandcamp integration, hardware experiment, or authorized effect.
**Branch base:** \`experiment/field-processor-001-go-static\` / STATIC-OS PR #87,
which itself builds on the native Instrument Host PR #54.
**Planner:** [planZ MASTER-SERVANT PR #12](https://github.com/the-static-collective/planZ/pull/12).

> THE SONG INVITES. THE SCORE PROPOSES. THE HUMAN OPENS THE DOOR.

## Source particulars, not inferred soundtrack identity

Three titles were read from the human-provided \`BandCamp (4).txt\` lyric
export. This fixture **recomposes songs from different releases** into a
new proposed listening score; it does not pretend they were all one original
album, that the export supplied verified recording bytes, or that anyone
heard them in this sequence.

1. **The House Takes Attendance** — \`The Autodiscography - The Road So Far\`,
   exported track/lyrics; album section does not itself prove physical-room sensing.
   Assigned role: SENSE.
2. **Tesla in the Orchard** — \`The Autodiscography - 183\`,
   a copper/speaker/orchard imaginative source, not a built sensor.
   Assigned role: ENCOUNTER.
3. **# mundaneWORMHOLE** — \`The Autodiscography - Creepy Disco\`,
   relevant as a narrative of two histories remaining distinct.
   Assigned role: PRESERVE.

**No exact Bandcamp song URLs, verified recording hashes, licensed derivative
audio files, or platform API credentials are claimed.** The synthetic score
can be bundled as a separate sidecar if the applicable publisher permits it.
Streaming transcodes are not a guaranteed carrier of embedded data.

## Implemented software

- \`instruments/bandcamp_field_score.py\` implements the existing
  \`InstrumentAdapterV0\`. It reports source SHA-256 of the exact *fixture bytes*
  and hands its candidate observations to the existing host.
- \`fixtures/bandcamp-field-score-001/three-cues.json\` declares a QR sighting,
  three *simulated* audio cue sightings, a repeated QR sighting, and one unrelated
  optical sighting. None is measured.
- \`tests/test_bandcamp_field_score_001.py\` provides negative/refusal and host
  integration cases. Run with
  \`python3 -m unittest discover -s tests -v\` in the actual stacked checkout.

The source schema is strictly synthetic-only. An occurrence needs its own ID,
channel, locally declared clock domain, sequence, integrity and referent.
Only declared PASS events pointing at the same exact referent become a candidate.
PASS here is a fixture label; it is NOT validation of a real decoder,
signature, audio capture, artist authorship, license or audience presence.

The two fixed proposal-only items are:

1. **Referent candidate** — QR and audio may resolve to the same declared
   artifact reference while retaining different occurrence IDs. Repeated QR
   observations remain visible. Neither equal refs nor equal lyrics prove
   independently sourced evidence.
2. **Sequence candidate** — three audio observations preserve missing,
   repeated, uncomparable-clock, or out-of-order status. A successful simulated
   order remains a *declared synthetic order*, not witnessed playback.

Both candidates are always HOLD or explicitly REFUSED. Even \`INSPECT\`
in the test source does not authorize effects. Native selection returns
\`may_open_url: false\`, \`may_download: false\`,
\`may_connect: false\`, \`may_execute: false\`.
The preexisting STATIC-OS host, not the score or the carrier, owns
any subsequent local state/receipt gate.

## Distinctions

\`\`\`text
LYRIC EXPORT != VERIFIED AUDIO FILE
TITLE MATCH != RECORDING IDENTITY
SCORE ORDER != PLAYBACK OBSERVATION
QR REPEAT != NEW AUTHORITY
SIMULATED PASS != PHYSICAL SIGNAL VERIFICATION
SAME REFERENT != INDEPENDENT WITNESSES
CUE != COMMAND
LOCAL READ != LOCAL ADMISSION
\`\`\`

## Independent next gates

- **F0 native CI:** verify tests on the exact branch, replay, selection,
  and source withdrawal on input mutation. No physical claims follow.
- **F1 printed-and-heard proof:** obtain owner-authorized WAV derivative,
  implement an independently specified audible low-bandwidth cue, print a
  standard QR with its quiet zone intact, and run 20 logged scans plus
  20 logged acoustic emit/capture trials. Save actual evidence hashes,
  missed matches, device conditions, and separate observation receipts.
  The tracks in this fixture are **not** claimed to contain such cues.
- **F2 human playback:** use local, opt-in player-state events (not scraping
  or silent microphones) to test repeated, skipped, paused, and out-of-order
  three-song playback. Offer one local view, with human inspect/decline
  gates and no implicit remote fetch.
- **Later:** Green Grammar sigil decoration outside standard QR bounds;
  separately approved sidecar exchange via LemonPRESS, Freeport, and reLATTE.
  A signature, if added, authenticates its declared issuer only.

The score is a portable invitation. Its absence does not restrict listening,
and the audio still makes complete sense without any compatible software.
