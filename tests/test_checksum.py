from __future__ import annotations

from app.modules.documents.checksum import sha256_hex


def test_sha256_hex_known_value() -> None:
    assert sha256_hex(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
