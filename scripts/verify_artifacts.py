#!/usr/bin/env python3
"""Verify published assembly hashes and the Pi 4 symbol-only import."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    artifacts = json.loads((ROOT / 'artifacts.json').read_text())
    for item in artifacts['artifacts']:
        if sha((ROOT / item['path']).read_bytes()) != item['sha256']:
            raise SystemExit('assembly hash mismatch: ' + item['path'])
    record = json.loads((ROOT / 'provenance/pi4-import.json').read_text())
    raw = (ROOT / record['output']).read_bytes()
    if sha(raw) != record['output_sha256']:
        raise SystemExit('Pi 4 publication hash mismatch')
    restored, count = re.subn(
        rb'\b_?invert25519\b',
        lambda match: b'_invert25519_x24_ff' if match.group().startswith(b'_') else b'invert25519_x24_ff',
        raw,
    )
    if count != record['transformation']['replacement_count'] or sha(restored) != record['upstream_sha256']:
        raise SystemExit('Pi 4 import changed more than public symbol tokens')
    provenance = (ROOT / record['slothy_provenance']).read_bytes()
    if sha(provenance) != record['slothy_provenance_sha256']:
        raise SystemExit('SLOTHY provenance hash mismatch')
    solver = json.loads(provenance)
    if solver['output']['sha256'] != record['upstream_sha256']:
        raise SystemExit('SLOTHY output mismatch')
    if solver['settings']['id'] != 'f1p5_r2_bottom':
        raise SystemExit('unexpected Pi 4 candidate')
    print('PASS: three published assembly files and exact symbol-only Pi 4 import.')


if __name__ == '__main__':
    main()
