#!/usr/bin/env python3
"""GENESIS-008: a portable proposal, a fictional festival, a useful old-machine museum.

Usage:
  python3 scripts/genesis008.py demo --out-dir NEW --focus "Festival Table"
  python3 scripts/genesis008.py inspect --text FILE.gc1
  python3 scripts/genesis008.py inspect --wav FILE.wav
  python3 scripts/genesis008.py import-legacy --input OLD_DEVICE_INTENT --out NEW.gc1
  python3 scripts/genesis008.py bridge --text DEVICE_ASK.gc1 --validate
  python3 scripts/genesis008.py bridge --text DEVICE_ASK.gc1 --execute --cannon ... --out NEW

No network calls. No automatic commands from cartridges. No signed witness.
"""
import argparse
import html
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cartridges import genesis008 as cart
from cartridges.audio import to_wav, from_wav


def must(condition, message):
    if not condition:
        raise ValueError("GENESIS008_REFUSED_" + message)


def create_only(path, bytes_):
    path = pathlib.Path(path)
    with path.open("xb") as file:
        file.write(bytes_)


def json_bytes(obj):
    return (json.dumps(obj, sort_keys=True, indent=2) + "\n").encode("utf8")


def station_roles(focus):
    return [
        {"station":"01 / THE QUESTION", "device":"GameCube or Wii",
         "kind":"ASK", "actual_hardware":"NOT_OBSERVED"},
        {"station":"02 / THE OFFER", "device":"Nintendo DS or Android",
         "kind":"OFFER", "actual_hardware":"NOT_OBSERVED"},
        {"station":"03 / THE PLAN", "device":"ESP32 or old laptop",
         "kind":"PROPOSE", "actual_hardware":"NOT_OBSERVED"},
        {"station":"04 / THE RECEIPT", "device":"CANNON-capable Raspberry Pi",
         "kind":"WITNESS", "actual_hardware":"NOT_OBSERVED"},
        {"station":"05 / THE NEXT FESTIVAL", "device":"Any printer / human handoff",
         "kind":"REPLICATE", "actual_hardware":"NOT_OBSERVED"},
    ]


def render_page(title, cards, footer):
    css = (
        "body{font:17px/1.5 system-ui,sans-serif;max-width:940px;margin:auto;"
        "padding:28px;color:#e2f2e5;background:#10271c}"
        "h1{font:3rem/1.1 Georgia,serif;color:#e0f4a3}h2{font:1.6rem Georgia,serif}"
        "article{border:1px solid #68957a;padding:20px;margin:18px 0;"
        "break-inside:avoid;background:#193629}"
        "small{color:#c6ddcc}code{overflow-wrap:anywhere}a{color:#dff1a4}"
        "@media print{body{color:black;background:white}article{background:white;"
        "border-color:black}small,h1,h2,a{color:black}}"
    )
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none';"
        "style-src 'unsafe-inline';base-uri 'none';form-action 'none'\">"
        "<title>" + html.escape(title) + "</title><style>" + css + "</style>"
        "</head><body><p>STATIC COLLECTIVE / GENESIS 008 / OFFLINE DEMONSTRATION</p>"
        "<h1>" + html.escape(title) + "</h1>" + cards +
        "<footer><p><small>" + html.escape(footer) +
        "</small></p></footer></body></html>\n"
    ).encode("utf8")


def load_registry():
    registry = json.loads((ROOT/"cartridges"/"organ-registry.json").read_text())
    must(registry["schema"] == "static-os.genesis-organ-registry/v1", "REGISTRY")
    must(len({x["id"] for x in registry["machines"]}) == len(registry["machines"]),
         "DUPLICATE_MACHINE")
    return registry


def demo(out_dir, focus, qr=False):
    must(focus in cart.FOCI, "UNKNOWN_FOCUS")
    target = pathlib.Path(out_dir)
    must(not target.exists() and target.parent.is_dir(), "OUTPUT_MUST_BE_NEW")
    registry = load_registry()
    items = []
    for i, kind in enumerate(cart.KINDS):
        parents = () if i == 0 else ((items[0]["digest"], items[-1]["digest"])
                                         if i > 1 else (items[0]["digest"],))
        # No artificial observer or validated actual result enters the chain.
        items.append(cart.mint(kind, focus, "FESTIVAL_SYNTHETIC_DEMO", parents))
    replay = cart.validate_chain(items)
    blueprint = {
        "schema":"static-os.genesis-replication-blueprint-candidate/v1",
        "source_cartridge":items[-1]["digest"],
        "source_proposal":items[2]["digest"],
        "stage":"DRAFT_NOT_AUTHORIZED",
        "event":"Next Community Build Gathering",
        "site":"NOT_SELECTED", "site_steward":"NOT_IDENTIFIED",
        "real_participants":0, "real_helpers":0, "approved_budget":None,
        "independent_evidence":False, "authorized_works":[],
        "conditions":["obtain site steward's permission",
                      "ask actual people for specific voluntary offers",
                      "write a bounded, reversible, accessible plan",
                      "check safe power, storage, transport and weather",
                      "make real observations with independently retained receipts",
                      "review what failed before proposing another event"],
        "next_step":"INVITE_INTEREST_ONLY_NO_DELIVERY_CLAIM",
    }
    event = {
        "schema":"static-os.genesis-festival-station-plan/v1",
        "focus":focus,"scenario":"FICTIONAL_DEMONSTRATION_NOT_AN_ACTUAL_EVENT",
        "steward_permission":"MISSING", "site_permission":"MISSING",
        "public_announcement_authorized":False, "fundraising_authorized":False,
        "actual_hardware_operated":False,
        "stations":station_roles(focus),
        "human_consent_model":"EACH_PERSON_OPT_IN_AND_FREE_TO_REFUSE",
        "receipts":"SOURCE_CODE_EXECUTION_NOT_PHYSICAL_SUCCESS",
    }
    rendered = ""
    for role, item in zip(event["stations"], items):
        kind = item["kind"]
        rendered += (
            "<article><p><small>" + html.escape(role["station"]) + "</small></p>"
            "<h2>" + html.escape(kind) + " — " + html.escape(role["device"]) + "</h2>"
            "<p>" + html.escape(item["statement"]) + "</p><p><strong>" +
            html.escape(item["disposition"]) + "</strong></p>"
            "<p><code>" + html.escape(item["digest"]) + "</code></p>"
            "<p><a href=\"" + kind.lower() + ".gc1\">Read portable text carrier</a>"
            " · <a href=\"" + kind.lower() + ".wav\">Hear WAV file carrier</a></p></article>"
        )
    festival_html = render_page(
        "The Festival That Starts Another Festival",
        "<p>Five reversible fictional stations. Every step creates an inspectable "
        "proposal, not an automatically executed order.</p>" + rendered,
        "NO REAL PEOPLE · NO SITE PERMISSION · NO PHYSICAL WITNESS · "
        "WITNESS HERE IS A HELD CLAIM, NOT VERIFIED DELIVERY."
    )
    museum_cards = "".join(
        "<article><h2>"+html.escape(x["label"])+"</h2><p><strong>"+
        html.escape(x["role"])+"</strong></p><p>"+
        html.escape(x["interface"])+"</p><p>Software: "+
        html.escape(x["software"])+"</p><p>Physical proof: "+
        html.escape(x["physical"])+"</p><small>Transfer: "+
        html.escape(x["transfer"])+"</small></article>"
        for x in registry["machines"]
    )
    museum_html = render_page(
        "The Museum of Unfinished Futures",
        "<p>These are manually catalogued possibilities. Nothing was scanned, "
        "repaired, donated, powered or field-tested by generating this page.</p>"
        + museum_cards,
        "REPAIR QUESTION != SAFE HARDWARE · CODE COMPILED != DEVICE TESTED · "
        "CHILD-FRIENDLY DEMONSTRATION != AUTOMATIC CONSENT."
    )
    outputs = {
        "festival.html":festival_html, "museum.html":museum_html,
        "cartridges.json":json_bytes(items), "station-plan.json":json_bytes(event),
        "replication-blueprint-candidate.json":json_bytes(blueprint),
        "chain-replay.json":json_bytes(replay),
        "readme.txt":(
            "GENESIS 008 / SYNTHETIC FESTIVAL, NOT A REAL EVENT\n"
            "Open festival.html and museum.html in a local browser or print them.\n"
            "Every .gc1 contains the entire digest-validated portable cartridge.\n"
            "Each .wav is a digital FSK file experiment; room/tape/audio-device "
            "transmission is untested.\nNo permission, transaction, identity, "
            "real hardware operation or field witness is asserted.\n"
        ).encode("utf8"),
    }
    for item in items:
        name = item["kind"].lower()
        outputs[name+".gc1"] = (cart.encode(item)+"\n").encode("ascii")
        outputs[name+".wav"] = to_wav(item)
    if qr:
        try:
            import segno
        except ImportError as error:
            raise ValueError("QR_REQUIRES_OPTIONAL_SEGNO_INSTALLED") from error
        # Save first ASK only; all further cartridges can be printed as
        # text or rendered with the same method if desired.
        with tempfile.TemporaryDirectory(prefix="genesis008-qr-") as staging:
            qrpath = pathlib.Path(staging)/"ask.svg"
            segno.make(cart.encode(items[0]), error="l").save(str(qrpath), scale=3)
            outputs["ask.svg"] = qrpath.read_bytes()
        must(b"<svg" in outputs["ask.svg"], "QR_SVG_EMPTY")
    target.mkdir(mode=0o700)
    for filename, blob in outputs.items():
        create_only(target/filename, blob)
    return {"status":"CREATED_SYNTHETIC_GENESIS008_FESTIVAL",
            "files":sorted(outputs), "chain":replay,
            "real_world_events":0, "physical_devices_tested":0}


def _import_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def legacy_to_cartridge(path):
    file = pathlib.Path(path)
    must(file.is_file() and file.stat().st_size <= 2048, "LEGACY_SIZE")
    value = json.loads(file.read_text(encoding="utf8"))
    must(isinstance(value, dict), "LEGACY_SHAPE")
    if value.get("schema") == "static-os.wii-first-boot-intent/v1":
        bridge = _import_module("original_wii", ROOT/"scripts"/"wii-to-cannon.py")
        bridge.validate(value)
        source = "NINTENDO_WII_SD"
    else:
        bridge = _import_module("original_portable", ROOT/"scripts"/"portable-to-cannon.py")
        bridge.validate(value)
        source = value["source_device"]
    must(value["question"] == cart.TOPICS[value["focus"]], "QUESTION_MISMATCH")
    return cart.mint("ASK", value["focus"], source)


def legacy_from_cartridge(value):
    cart.validate(value)
    must(value["kind"] == "ASK" and not value["parents"], "ONLY_ORIGINAL_ASK_ACCEPTED")
    if value["source"] == "NINTENDO_WII_SD":
        bridge = _import_module("original_wii", ROOT/"scripts"/"wii-to-cannon.py")
        result = {
            "schema":bridge.SCHEMA, "mission":"living-house",
            "focus":value["focus"],"question":value["statement"],
            "scenario":"FICTIONAL_A_B","mode":"OFFLINE_HOLD_ONLY",
            "source_device":"WII_HOMEBREW_LOCAL_OPERATOR",
            "operator_action":"PLUS_EXPORT_PRESSED",
            "status":"PROPOSAL_ONLY_NOT_EXECUTED",
            "transmitted":False, "physical_observation":False,
            "signed":False, "independent_witness":False,
        }
    else:
        bridge = _import_module("original_portable", ROOT/"scripts"/"portable-to-cannon.py")
        must(value["source"] in bridge.DEVICES,
             "SYNTHETIC_OR_UNKNOWN_DEVICE_CANNOT_BRIDGE")
        result = bridge.make_intent(value["source"], value["focus"])
    bridge.validate(result)
    return result


def bridge_to_cannon(text, args):
    ask = cart.decode(text)
    legacy = legacy_from_cartridge(ask)
    if not args.execute:
        return {"status":"VALID_INERT_CARTRIDGE_FOR_ORIGINAL_CANNON",
                "focus":ask["focus"], "device_claim":ask["source"],
                "executed":False, "signed":False}
    needed = ("cannon","staticos","webz","gro","ghot","jarvis","out")
    must(all(getattr(args, name, None) for name in needed), "REQUIRES_EXPLICIT_SOURCE_PATHS")
    with tempfile.TemporaryDirectory(prefix="genesis008-cartridge-") as tmp:
        jsonpath = pathlib.Path(tmp)/"original-intent.json"
        create_only(jsonpath, json_bytes(legacy))
        runner = ("wii-to-cannon.py" if ask["source"] == "NINTENDO_WII_SD"
                  else "portable-to-cannon.py")
        cmd = [sys.executable, str(ROOT/"scripts"/runner),
               "--intent", str(jsonpath), "--execute"]
        for name in needed:
            cmd += ["--"+name, getattr(args, name)]
        subprocess.run(cmd, check=True, timeout=180)
    return {"status":"EXPLICIT_ORIGINAL_CANNON_SOFTWARE_EXECUTION_COMPLETED",
            "source_cartridge":ask["digest"],"physical_world_changed":False,
            "human_witness_verified":False,"output":args.out}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest="mode", required=True)
    demo_p = subs.add_parser("demo")
    demo_p.add_argument("--out-dir",required=True)
    demo_p.add_argument("--focus",choices=cart.FOCI,default="Festival Table")
    demo_p.add_argument("--qr",action="store_true",
                        help="Optional first-ASK QR SVG via build-time segno")
    view = subs.add_parser("inspect")
    v = view.add_mutually_exclusive_group(required=True)
    v.add_argument("--text")
    v.add_argument("--wav")
    old = subs.add_parser("import-legacy")
    old.add_argument("--input",required=True)
    old.add_argument("--out",required=True)
    bridge = subs.add_parser("bridge")
    bridge.add_argument("--text",required=True)
    mode = bridge.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate",action="store_true")
    mode.add_argument("--execute",action="store_true")
    for name in ("cannon","staticos","webz","gro","ghot","jarvis","out"):
        bridge.add_argument("--"+name)
    args = p.parse_args(argv)
    try:
        if args.mode == "demo":
            result = demo(args.out_dir,args.focus,args.qr)
        elif args.mode == "inspect":
            if args.text:
                file = pathlib.Path(args.text)
                must(file.is_file() and file.stat().st_size <= cart.MAX_TEXT+2,
                     "TEXT_FILE_TOO_LARGE")
                value = cart.decode(file.read_text(encoding="ascii").strip())
            else:
                file = pathlib.Path(args.wav)
                must(file.is_file() and file.stat().st_size <= 3_000_000,
                     "WAV_FILE_TOO_LARGE")
                value = from_wav(file.read_bytes())
            result = {"status":"DIGEST_VALID_PROPOSAL_ONLY","cartridge":value,
                      "physical_sound_transfer_tested":False}
        elif args.mode == "import-legacy":
            value = legacy_to_cartridge(args.input)
            create_only(args.out,(cart.encode(value)+"\n").encode("ascii"))
            result = {"status":"EXISTING_PORTABLE_SOURCE_CONVERTED",
                      "cartridge":value["digest"], "executed":False}
        else:
            file=pathlib.Path(args.text)
            must(file.is_file() and file.stat().st_size <= cart.MAX_TEXT+2,
                 "BRIDGE_CARRIER_TOO_LARGE")
            result=bridge_to_cannon(file.read_text(encoding="ascii").strip(),args)
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    except (OSError,ValueError,UnicodeError,json.JSONDecodeError,
            subprocess.TimeoutExpired,subprocess.CalledProcessError) as error:
        print("HOLD: "+str(error)[:500],file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
