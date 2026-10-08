#!/usr/bin/env python3
"""Install the bounded Python instrument host into an explicit local prefix.

No services are started, foreign organs installed, keys imported, or capabilities granted.
Native donor roots remain explicit runtime inputs. No RF adapter is shipped.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def install(prefix: Path) -> Path:
    manifest = json.loads((ROOT / "manifest/instrument-host-001.json").read_text())
    for name, expected in manifest["oracle"]["sha256"].items():
        actual = sha256((ROOT / manifest["oracle"]["path"] / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("ELEVEN-HEAP oracle changed: " + name)
    if sha256((ROOT / manifest["fixture"]["path"]).read_bytes()).hexdigest() != manifest["fixture"]["sha256"]:
        raise ValueError("recorded fixture changed")
    target = prefix.resolve() / "lib/static-os/instrument-host"
    if target.exists():
        raise ValueError("instrument host target already exists; use a fresh prefix")
    target.mkdir(parents=True)
    for directory in ("instruments", "vendor/eleven_heap_001", "fixtures/instrument-host-001"):
        shutil.copytree(ROOT / directory, target / directory,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "artifacts"))
    (target / "manifest").mkdir()
    shutil.copyfile(ROOT / "manifest/instrument-host-001.json", target / "manifest/instrument-host-001.json")
    executable = prefix.resolve() / "bin/static-instrument"
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.write_text("""#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib/static-os/instrument-host'))
from instruments.cli import main
raise SystemExit(main())
""")
    executable.chmod(0o755)
    return executable


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", required=True, type=Path)
    args = parser.parse_args()
    print(install(args.prefix))
