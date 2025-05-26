class FhirClient:
    """Lightweight client for basic FHIR operations."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def get_patient(self, patient_id: str) -> dict:
        import requests
        url = f"{self.base_url}/Patient/{patient_id}"
        resp = requests.get(url, headers=self._headers())
        if not 200 <= resp.status_code < 300:
            resp.raise_for_status()
        return resp.json()

    def search_observations(self, patient_id: str) -> list[dict]:
        import requests
        url = f"{self.base_url}/Observation"
        params = {"subject": f"Patient/{patient_id}"}
        resp = requests.get(url, headers=self._headers(), params=params)
        if not 200 <= resp.status_code < 300:
            resp.raise_for_status()
        data = resp.json()
        return data.get("entry", [])

    def create_resource(self, resource_type: str, body: dict) -> dict:
        import requests
        url = f"{self.base_url}/{resource_type}"
        resp = requests.post(url, headers=self._headers(), json=body)
        if not 200 <= resp.status_code < 300:
            resp.raise_for_status()
        return resp.json()
