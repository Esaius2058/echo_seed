import os
import httpx

class HFClient:
    def __init__(self):
        self.token = os.getenv("HUGGINGFACE_API_TOKEN")
        if not self.token:
            raise ValueError("HUGGINGFACE_API_TOKEN is missing in .env")
        self.headers = {"Authorization": f"Bearer ${self.token}"}
        # Increased timeout because inference takes time
        self.client = httpx.Client(timeout=60.0)

    def get_mert_embedding(self, audio_bytes: bytes) -> list[float]:
        url = "https://api-inference.huggingface.co/models/m-a-p/MERT-v1-95M"
        response = self.client.post(url, headers=self.headers, content=audio_bytes)
        response.raise_for_status()

        result = response.json()
        # Ensure it returns the expected 768-dim list, adjust based on exact HF output wrapper
        if isinstance(result, list) and isinstance(result[0], list):
            return result[0]
        return result

    def get_tempo_and_key(self):
        return self.token

    def get_valence_arousal(self):
        return self.token

