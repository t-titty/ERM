import types
import sys

import pytest

from .client import FhirClient


def _install_requests(monkeypatch, get=None, post=None):
    mock = types.SimpleNamespace()
    if get:
        mock.get = get
    if post:
        mock.post = post
    monkeypatch.setitem(sys.modules, 'requests', mock)


def test_init_properties():
    client = FhirClient('http://server/', 'abc')
    assert client.base_url == 'http://server'
    assert client.api_key == 'abc'


def test_get_patient(monkeypatch):
    class Resp:
        status_code = 200

        def json(self):
            return {'id': '1'}

    def mock_get(url, headers):
        assert url == 'http://server/Patient/1'
        assert headers['Authorization'] == 'Bearer abc'
        return Resp()

    _install_requests(monkeypatch, get=mock_get)
    client = FhirClient('http://server', 'abc')
    patient = client.get_patient('1')
    assert patient == {'id': '1'}


def test_search_observations(monkeypatch):
    class Resp:
        status_code = 200

        def json(self):
            return {'entry': [{'id': 'o1'}]}

    def mock_get(url, headers, params):
        assert url == 'http://server/Observation'
        assert params == {'subject': 'Patient/1'}
        assert headers['Authorization'] == 'Bearer abc'
        return Resp()

    _install_requests(monkeypatch, get=mock_get)
    client = FhirClient('http://server', 'abc')
    obs = client.search_observations('1')
    assert obs == [{'id': 'o1'}]


def test_create_resource(monkeypatch):
    class Resp:
        status_code = 201

        def json(self):
            return {'id': '2'}

    def mock_post(url, headers, json):
        assert url == 'http://server/Patient'
        assert headers['Authorization'] == 'Bearer abc'
        assert json == {'name': 'Bob'}
        return Resp()

    _install_requests(monkeypatch, post=mock_post)
    client = FhirClient('http://server', 'abc')
    result = client.create_resource('Patient', {'name': 'Bob'})
    assert result == {'id': '2'}
