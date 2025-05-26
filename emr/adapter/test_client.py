import types

import pytest

from emr.adapter import client as client_module
from emr.adapter.client import Client


class DummyResponse:
    def __init__(self, json_data):
        self._json = json_data
        self.status_code = 200

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


class DummySession:
    def __init__(self):
        self.last_post = None
        self.last_get = None
        self.response = DummyResponse({})

    def post(self, url, json):
        self.last_post = (url, json)
        return self.response

    def get(self, url, params=None):
        self.last_get = (url, params)
        return self.response


def test_create_resource_encrypt(monkeypatch):
    session = DummySession()
    client = Client("http://example.com", kek_uri="kek://uri", session=session)

    ciphertext = {"cipher": True}

    def fake_encrypt_resource(body, kek_uri):
        assert body == {"foo": "bar"}
        assert kek_uri == "kek://uri"
        return ciphertext

    monkeypatch.setattr(client_module, "encrypt_resource", fake_encrypt_resource)

    client.create_resource("Patient", {"foo": "bar"})

    assert session.last_post[0] == "http://example.com/Patient"
    assert session.last_post[1] == ciphertext


def test_get_patient_decrypt(monkeypatch):
    session = DummySession()
    session.response = DummyResponse({"ciphertext": True})
    client = Client("http://example.com", kek_uri="kek://uri", session=session)

    plaintext = {"patient": "data"}

    def fake_decrypt_resource(blob, kek_uri):
        assert blob == {"ciphertext": True}
        assert kek_uri == "kek://uri"
        return plaintext

    monkeypatch.setattr(client_module, "decrypt_resource", fake_decrypt_resource)

    result = client.get_patient("123")

    assert session.last_get[0] == "http://example.com/Patient/123"
    assert result == plaintext


def test_search_observations_decrypt(monkeypatch):
    session = DummySession()
    session.response = DummyResponse({"ciphertext": True})
    client = Client("http://example.com", kek_uri="kek://uri", session=session)

    plaintext = {"observations": [1, 2]}

    def fake_decrypt_resource(blob, kek_uri):
        assert blob == {"ciphertext": True}
        assert kek_uri == "kek://uri"
        return plaintext

    monkeypatch.setattr(client_module, "decrypt_resource", fake_decrypt_resource)

    result = client.search_observations({"patient": "123"})

    assert session.last_get == ("http://example.com/Observation", {"patient": "123"})
    assert result == plaintext
