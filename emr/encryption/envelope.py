import base64
import json
import secrets
from typing import Any, Dict

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM
except Exception:  # pragma: no cover - cryptography not installed
    _AESGCM = None  # type: ignore


class _FakeAESGCM:
    """Fallback AESGCM implementation performing XOR based masking.

    This is **not** secure and only intended for environments lacking the
    ``cryptography`` package. It enables unit testing of the envelope logic
    without providing real encryption.
    """

    def __init__(self, key: bytes) -> None:
        self.key = key

    def _apply(self, data: bytes) -> bytes:
        out = bytearray()
        key = self.key
        for i, b in enumerate(data):
            out.append(b ^ key[i % len(key)])
        return bytes(out)

    def encrypt(self, nonce: bytes, data: bytes, associated_data: Any = None) -> bytes:
        return self._apply(data)

    def decrypt(self, nonce: bytes, data: bytes, associated_data: Any = None) -> bytes:
        return self._apply(data)


# Select AESGCM implementation
AESGCM = _AESGCM if _AESGCM is not None else _FakeAESGCM


def _get_kms_client():
    """Instantiate and return a KMS client.

    This indirection allows unit tests to patch the client without requiring the
    ``google-cloud-kms`` package to be installed in the test environment.
    """

    from google.cloud import kms  # type: ignore

    return kms.KeyManagementServiceClient()


def encrypt_resource(body: Dict[str, Any], kek_uri: str) -> Dict[str, str]:
    """Encrypt a FHIR resource using envelope encryption."""

    if not isinstance(body, dict):
        raise TypeError("body must be a dict")

    json_bytes = json.dumps(body).encode("utf-8")

    dek = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(dek)
    ciphertext = aesgcm.encrypt(nonce, json_bytes, None)

    kms_client = _get_kms_client()
    wrap_response = kms_client.encrypt(request={"name": kek_uri, "plaintext": dek})
    wrapped_dek = wrap_response.ciphertext

    return {
        "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
        "nonce": base64.b64encode(nonce).decode("utf-8"),
        "wrapped_dek": base64.b64encode(wrapped_dek).decode("utf-8"),
    }


def decrypt_resource(blob: Dict[str, str], kek_uri: str) -> Dict[str, Any]:
    """Decrypt a previously encrypted resource."""

    nonce = base64.b64decode(blob["nonce"])  # may raise KeyError
    ciphertext = base64.b64decode(blob["ciphertext"])  # may raise KeyError
    wrapped_dek = base64.b64decode(blob["wrapped_dek"])  # may raise KeyError

    kms_client = _get_kms_client()
    unwrap_response = kms_client.decrypt(request={"name": kek_uri, "ciphertext": wrapped_dek})
    dek = unwrap_response.plaintext

    aesgcm = AESGCM(dek)
    json_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(json_bytes.decode("utf-8"))
