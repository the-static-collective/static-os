import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {webcrypto} from "node:crypto";
import {
  buildLead, photoEvidence, cautionCodes, affordancesFor,
  validLandsFor, imageFormat, SOURCE_LAND, CATEGORIES, HAZARDS,
} from "../forage/mobile/scout-core.mjs";

const example = {
  description: "Discarded-looking motor assembly, ownership unconfirmed",
  observation: "Visible from sidewalk, no item touched or removed",
  source_kind: "UNKNOWN", land_class: "UNKNOWN", category: "TECH_PARTS",
  site_ref: "unknown:site", steward_ref: "unknown:steward",
  purpose: "COMMUNITY_NONCOMMERCIAL", amount: "1", unit: "ITEM",
  hazards: ["BATTERY_PRESENT"],
};
const png = new Uint8Array([137,80,78,71,13,10,26,10,0,0,0,0,0,0,0,0]);
const jpeg = new Uint8Array([255,216,255,0,0,0,0,0,0,0,0,0,0]);
const lead = () => buildLead(example, "test-id-001");

test("human-selected phone lead satisfies exact 001 schema and remains unowned", () => {
  const record = lead();
  assert.deepEqual(Object.keys(record).sort(), [
    "schema", "lead_ref", "item_ref", "description", "category",
    "source_kind", "land_class", "site_ref", "steward_ref",
    "purpose", "quantity", "hazards", "observation",
    "operator_claim_of_ownership",
  ].sort());
  assert.equal(record.schema, "static-os.forage-lead/v0");
  assert.equal(record.lead_ref, "scout:test-id-001");
  assert.equal(record.item_ref, "scout:item-test-id-001");
  assert.equal(record.operator_claim_of_ownership, false);
  assert.deepEqual(record.quantity, {amount:1,unit:"ITEM"});
  assert.deepEqual(record.hazards, ["BATTERY_PRESENT"]);
  assert.ok(cautionCodes(record).includes("NO_SCOPED_AUTHORITY_REVIEW"));
  assert.ok(cautionCodes(record).includes("OWNERSHIP_UNKNOWN_NO_PICKUP"));
  assert.ok(cautionCodes(record).includes("PHYSICAL_SAFETY_INSPECTION_NEEDED"));
});

test("source-to-land rules block authority mismatches", () => {
  assert.deepEqual(validLandsFor("DIRECT_OWNER_OFFER"), ["PRIVATE"]);
  assert.deepEqual(validLandsFor("MUNICIPAL_REUSE"), ["MUNICIPAL"]);
  assert.throws(() => buildLead({...example,source_kind:"DIRECT_OWNER_OFFER", land_class:"BLM"}, "id-001"));
  assert.throws(() => buildLead({...example,source_kind:"PUBLIC_LAND_COLLECTION", land_class:"PRIVATE"}, "id-002"));
  assert.throws(() => buildLead({...example,category:"DIGITAL_MATERIAL",source_kind:"PUBLIC_LAND_COLLECTION",land_class:"BLM"}, "id-003"));
  assert.equal(Object.keys(SOURCE_LAND).length, 6);
});

test("unknown hazards never become safe certification", () => {
  const base = buildLead({...example,hazards:[]}, "id-004");
  assert.deepEqual(base.hazards, []);
  assert.ok(cautionCodes(base).includes("NO_SCOPED_AUTHORITY_REVIEW"));
  const unsafe = buildLead({...example,hazards:["LOCKED_CONTAINER","DAMAGED_LITHIUM"]}, "id-005");
  assert.ok(cautionCodes(unsafe).includes("STOP_LOCKED_CONTAINER"));
  assert.ok(cautionCodes(unsafe).includes("STOP_DAMAGED_LITHIUM"));
  assert.equal(HAZARDS.length, 14);
});

test("no fake or extra collection rights and bounded values", () => {
  assert.throws(() => buildLead({...example,amount:0}, "id-006"));
  assert.throws(() => buildLead({...example,amount:1.25}, "id-007"));
  assert.throws(() => buildLead({...example,amount:"NaN"}, "id-008"));
  assert.throws(() => buildLead({...example,hazards:["SOME_MAGIC_RIGHT"]}, "id-009"));
  assert.throws(() => buildLead({...example,hazards:["BATTERY_PRESENT","BATTERY_PRESENT"]}, "id-010"));
  assert.throws(() => buildLead({...example,description:"a"}, "id-011"));
  assert.throws(() => buildLead({...example,site_ref:"no spaces allowed"}, "id-012"));
  assert.equal(CATEGORIES.length, 7);
});

test("category affordance labels are non-executing, and categories unknown fail", () => {
  assert.deepEqual(affordancesFor("TECH_PARTS"), [
    "Bracket or fixture candidate", "Motor/drive research",
    "Fastener recovery check",
  ]);
  assert.ok(affordancesFor("FOOD").includes("Do not taste to identify"));
  assert.throws(() => affordancesFor("I_SAW_A_REAL_MOTOR"));
  assert.throws(() => validLandsFor("I_OWN_THE_CURB"));
});

test("photo evidence hashes original bytes and never authenticates device or rights", async () => {
  const witness = await photoEvidence(png, lead().lead_ref, webcrypto.subtle);
  assert.equal(witness.schema, "static-os.forage-photo-evidence/v0");
  assert.equal(witness.lead_ref, "scout:test-id-001");
  assert.equal(witness.original_byte_count, png.length);
  assert.equal(witness.original_bytes_sha256.length, 64);
  assert.equal(witness.content_type, "image/png");
  for (const flag of ["device_authenticated","camera_capture_authenticated",
      "rights_inferred_from_photo","hazards_screened_by_machine",
      "photo_included_in_receipt"]) assert.equal(witness[flag], false);
  assert.equal(imageFormat(jpeg), "image/jpeg");
  const different = await photoEvidence(jpeg, lead().lead_ref, webcrypto.subtle);
  assert.notEqual(witness.original_bytes_sha256, different.original_bytes_sha256);
});

test("refuse unsupported camera image and oversize media", async () => {
  assert.throws(() => imageFormat(new Uint8Array(12)));
  await assert.rejects(photoEvidence(new Uint8Array(17*1024*1024),
                                    lead().lead_ref, webcrypto.subtle));
  await assert.rejects(photoEvidence(new Uint8Array([1,2]),
                                    lead().lead_ref, webcrypto.subtle));
});

test("mobile page has capture and no network dependency or geolocation side channel", () => {
  const html = readFileSync(new URL("../forage/mobile/index.html", import.meta.url), "utf8");
  const app = readFileSync(new URL("../forage/mobile/app.mjs", import.meta.url), "utf8");
  assert.match(html, /capture="environment"/);
  assert.match(html, /connect-src 'none'/);
  assert.match(html, /FORAGE-002/);
  assert.match(html, /collection NOT authorized/);
  assert.doesNotMatch(app, /\bfetch\(|XMLHttpRequest|sendBeacon|geolocation|localStorage|WebSocket/);
  assert.match(app, /scout-core\.mjs/);
  assert.match(app, /save-photo/);
});
