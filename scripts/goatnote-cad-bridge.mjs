#!/usr/bin/env node
/* GOATnote owns journal projection. Static-OS calls this exact pinned native
 * module; no local duplicate implementation and no browser data mutation.
 */
import { readFile } from "node:fs/promises";
import {
  verifyCadJournalHandoff, projectCadJournal
} from "../external/GOATnote/cad-journal.mjs";

try {
  if (process.argv.length !== 3) throw Error("EXACT_GOATNOTE_HANDOFF_PATH_REQUIRED");
  const handoff=JSON.parse(await readFile(process.argv[2],"utf8"));
  verifyCadJournalHandoff(handoff);
  const note=projectCadJournal(handoff);
  if (note.cadJournal.goatnote_signature_verified !== false
      || note.cadJournal.upstream_native_verified !== true
      || note.returnThreads.length !== 1
      || note.margins.length !== 12
      || note.versions.length !== 1) {
    throw Error("NATIVE_GOATNOTE_JOURNAL_PROJECTION_INVALID");
  }
  const source=note.versions[0];
  for (const margin of note.margins) {
    const a=margin.anchor;
    if (margin.versionId!==source.id
        || source.text.slice(a.start,a.end)!==a.quote) {
      throw Error("GOATNOTE_MARGIN_SOURCE_MISMATCH");
    }
  }
  process.stdout.write(JSON.stringify({
    schema:"static-os.goatnote-journal-preview/v0",
    native_goatnote_module:"cad-journal.mjs",
    source_note:note,
    import_status:"CANDIDATE_ONLY",
    browser_notebook_modified:false
  })+"\n");
} catch (error) {
  process.stderr.write("GOATNOTE_HOLD: "+String(error).slice(0,260)+"\n");
  process.exitCode=2;
}
