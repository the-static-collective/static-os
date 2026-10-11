"""F1 digital coupon verification: no physical emission, QR scan, or mic capture claimed."""
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
import sys
import unittest
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from singing_sigil_f1 import (PAYLOAD, DTMF_KEYS, FS, payload_to_keys,
                              keys_to_payload, verify_payload, synthesize,
                              decode_wav, write_wav, make_coupon)


class CouponTests(unittest.TestCase):
    def test_payload_and_crc(self):
        self.assertTrue(verify_payload(PAYLOAD))
        self.assertFalse(verify_payload(PAYLOAD[:-1] + ('0' if PAYLOAD[-1] != '0' else '1')))
        self.assertFalse(verify_payload('SCF1:SS001:00000000'))

    def test_nibble_mapping_roundtrip(self):
        self.assertEqual(keys_to_payload(payload_to_keys(PAYLOAD)), PAYLOAD)
        self.assertIsNone(keys_to_payload('X'))
        self.assertIsNone(keys_to_payload('1'))

    def test_reproducible_waveform(self):
        self.assertEqual(hashlib.sha256(synthesize()).digest(),
                         hashlib.sha256(synthesize()).digest())

    def test_roundtrip_two_packets(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'cue.wav'
            write_wav(file, synthesize())
            result = decode_wav(file)
            self.assertEqual(result['status'], 'CANDIDATE_ONLY')
            self.assertEqual([x['payload'] for x in result['valid_packets']], [PAYLOAD, PAYLOAD])
            self.assertEqual(result['authority'], 'NONE')
            self.assertEqual(result['physical_playback_witness'], 'NOT_ESTABLISHED')

    def test_single_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'single.wav'
            write_wav(file, synthesize(repeats=1))
            self.assertEqual(len(decode_wav(file)['valid_packets']), 1)

    def test_silence_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'quiet.wav'
            write_wav(file, b'\x00\x00' * (FS * 2))
            self.assertEqual(decode_wav(file)['status'], 'NO_VALID_PACKET')

    def test_shifted_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'shift.wav'
            write_wav(file, b'\x00\x00' * 12347 + synthesize())
            result = decode_wav(file)
            self.assertEqual([x['payload'] for x in result['valid_packets']], [PAYLOAD, PAYLOAD])

    def test_limited_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'stereo.wav'
            with wave.open(str(file), 'wb') as w:
                w.setnchannels(2)
                w.setsampwidth(2)
                w.setframerate(FS)
                w.writeframes(b'\0\0\0\0' * 10)
            with self.assertRaises(ValueError):
                decode_wav(file)

    def test_coupon_manifest_points_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = make_coupon(Path(tmp))
            wav = Path(tmp) / 'singing-sigil-f1-dtmf.wav'
            self.assertEqual(m['wav_sha256'], hashlib.sha256(wav.read_bytes()).hexdigest())
            self.assertEqual(m['payload'], (Path(tmp) / 'singing-sigil-f1-payload.txt').read_text().strip())
            self.assertFalse(m['auto_execution'])


if __name__ == '__main__':
    unittest.main()
