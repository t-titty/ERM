"""Simple EMR client with optional envelope encryption."""

from typing import Any, Dict, Optional, Protocol

from emr.encryption.envelope import encrypt_resource, decrypt_resource


class SessionProtocol(Protocol):
    def post(self, url: str, json: Dict[str, Any]):
        ...

    def get(self, url: str, params: Optional[Dict[str, Any]] = None):
        ...


class _DefaultSession:
    """Session used when none is provided. Methods raise NotImplementedError."""

    def post(self, url: str, json: Dict[str, Any]):
        raise NotImplementedError("HTTP POST not implemented")

    def get(self, url: str, params: Optional[Dict[str, Any]] = None):
        raise NotImplementedError("HTTP GET not implemented")


class Client:
    """HTTP client for interacting with an EMR FHIR API."""

    def __init__(self, base_url: str, kek_uri: Optional[str] = None, session: Optional[SessionProtocol] = None) -> None:
        self.base_url = base_url.rstrip('/')
        self.kek_uri = kek_uri
        self.session: SessionProtocol = session or _DefaultSession()

    def create_resource(self, resource_type: str, body: Dict[str, Any]):
        url = f"{self.base_url}/{resource_type}"
        payload = body
        if self.kek_uri:
            payload = encrypt_resource(body, self.kek_uri)
        return self.session.post(url, json=payload)

    def get_patient(self, patient_id: str):
        url = f"{self.base_url}/Patient/{patient_id}"
        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()
        if self.kek_uri:
            data = decrypt_resource(data, self.kek_uri)
        return data

    def search_observations(self, params: Dict[str, Any]):
        url = f"{self.base_url}/Observation"
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if self.kek_uri:
            data = decrypt_resource(data, self.kek_uri)
        return data
