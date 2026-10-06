import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "physical-boot-receipt.py"
SPEC = importlib.util.spec_from_file_location("physical_boot_receipt", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

SHA40_A = "a" * 40
SHA40_B = "b" * 40
SHA256 = "c" * 64


def valid_receipt():
    return {
        "schema": MODULE.SCHEMA,
        "experiment": MODULE.EXPERIMENT,
        "receipt_status": "observed",
        "source": {
            "repository": MODULE.REPOSITORY,
            "commit": SHA40_A,
            "house_commit": SHA40_B,
        },
        "iso": {
            "filename": "live-image-amd64.hybrid.iso",
            "sha256": SHA256,
            "bytes": 123456,
        },
        "vm": {
            "bios_boot": True,
            "uefi_boot": True,
            "offline_house": True,
        },
        "physical": {
            "medium": "usb",
            "observed_boot": True,
            "desktop_visible": True,
            "house_loopback": True,
            "network_disconnected": True,
            "installer_invoked": False,
            "internal_storage_written_by_operator": False,
        },
        "witness": {
            "kind": "human",
            "name": "operator",
            "observed_at": "2026-10-06T18:30:00-05:00",
            "statement": "Observed cold USB boot and offline HOUSE loopback.",
        },
        "nonclaims": {
            "installed_os": False,
            "persistent_cross_boot": "not_proven",
        },
    }


class PhysicalBootReceiptTests(unittest.TestCase):
    def test_accepts_complete_observed_receipt(self):
        self.assertEqual(MODULE.validate(valid_receipt())["receipt_status"], "observed")

    def test_refuses_candidate_as_observation(self):
        value = valid_receipt()
        value["receipt_status"] = "candidate"
        with self.assertRaisesRegex(ValueError, "receipt_status"):
            MODULE.validate(value)

    def test_refuses_missing_physical_boot(self):
        value = valid_receipt()
        value["physical"]["observed_boot"] = False
        with self.assertRaisesRegex(ValueError, "physical.observed_boot"):
            MODULE.validate(value)

    def test_refuses_installer_invocation(self):
        value = valid_receipt()
        value["physical"]["installer_invoked"] = True
        with self.assertRaisesRegex(ValueError, "installer"):
            MODULE.validate(value)

    def test_refuses_agent_witness(self):
        value = valid_receipt()
        value["witness"]["kind"] = "agent"
        with self.assertRaisesRegex(ValueError, "human"):
            MODULE.validate(value)

    def test_refuses_installed_os_promotion(self):
        value = valid_receipt()
        value["nonclaims"]["installed_os"] = True
        with self.assertRaisesRegex(ValueError, "installed_os"):
            MODULE.validate(value)

    def test_refuses_cross_boot_persistence_promotion(self):
        value = valid_receipt()
        value["nonclaims"]["persistent_cross_boot"] = "proven"
        with self.assertRaisesRegex(ValueError, "persistent"):
            MODULE.validate(value)

    def test_rfc3339_requires_timezone(self):
        value = valid_receipt()
        value["witness"]["observed_at"] = "2026-10-06T18:30:00"
        with self.assertRaisesRegex(ValueError, "RFC3339"):
            MODULE.validate(value)


if __name__ == "__main__":
    unittest.main()
