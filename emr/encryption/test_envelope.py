import base64
from types import SimpleNamespace

import pytest

from emr.encryption import envelope


class DummyAESGCM:
    def __init__(self, key: bytes) -> None:
        self.key = key

    def _apply(self, data: bytes) -> bytes:
        out = bytearray()
        for i, b in enumerate(data):
            out.append(b ^ self.key[i % len(self.key)])
        return bytes(out)

    def encrypt(self, nonce: bytes, data: bytes, associated_data=None) -> bytes:
        return self._apply(data)

    def decrypt(self, nonce: bytes, data: bytes, associated_data=None) -> bytes:
        return self._apply(data)


class FakeKMSClient:
    def encrypt(self, request):
        return SimpleNamespace(ciphertext=request["plaintext"][::-1])

    def decrypt(self, request):
        return SimpleNamespace(plaintext=request["ciphertext"][::-1])


def setup_module(module):
    envelope.AESGCM = DummyAESGCM  # patch AESGCM fallback


def test_encrypt_decrypt_roundtrip(monkeypatch):
    monkeypatch.setattr(envelope, "_get_kms_client", lambda: FakeKMSClient())
    body = {"foo": "bar"}
    kek_uri = "projects/test"

    blob = envelope.encrypt_resource(body, kek_uri)

    assert set(blob.keys()) == {"ciphertext", "nonce", "wrapped_dek"}

    out = envelope.decrypt_resource(blob, kek_uri)
    assert out == body


def test_decrypt_missing_fields(monkeypatch):
    monkeypatch.setattr(envelope, "_get_kms_client", lambda: FakeKMSClient())
    blob = {"ciphertext": "", "nonce": ""}
    with pytest.raises(KeyError):
        envelope.decrypt_resource(blob, "uri")
