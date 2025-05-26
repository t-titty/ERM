"""Envelope encryption utilities."""

import base64
import json
import secrets
from typing import Any, Dict

try:
    # Allow tests to patch AESGCM by handling ImportError generically
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception:  # pragma: no cover - fallback for test patching
    AESGCM = None  # type: ignore

import google.cloud.kms


def encrypt_resource(body: Dict[str, Any], kek_uri: str) -> Dict[str, str]:
    """Encrypt a resource dictionary using envelope encryption."""
    if not isinstance(body, dict):
        raise TypeError("body must be a dict")

    json_bytes = json.dumps(body).encode("utf-8")

    dek = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)

    ciphertext = AESGCM(dek).encrypt(nonce, json_bytes, None)

    kms = google.cloud.kms.KeyManagementServiceClient()
    wrapped = kms.encrypt(request={"name": kek_uri, "plaintext": dek}).ciphertext

    return {
        "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
        "nonce": base64.b64encode(nonce).decode("utf-8"),
        "wrapped_dek": base64.b64encode(wrapped).decode("utf-8"),
    }


def decrypt_resource(blob: Dict[str, str], kek_uri: str) -> Dict[str, Any]:
    """Decrypt an envelope encrypted resource."""
    nonce = base64.b64decode(blob["nonce"])
    ciphertext = base64.b64decode(blob["ciphertext"])
    wrapped = base64.b64decode(blob["wrapped_dek"])

    kms = google.cloud.kms.KeyManagementServiceClient()
    dek = kms.decrypt(request={"name": kek_uri, "ciphertext": wrapped}).plaintext

    json_bytes = AESGCM(dek).decrypt(nonce, ciphertext, None)
    return json.loads(json_bytes.decode("utf-8"))
