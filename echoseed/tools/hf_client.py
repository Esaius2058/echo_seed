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

        # Try up to 3 times to account for model loading
        for attempt in range(3):
            response = self.client.post(url, headers=self.headers, content=audio_bytes)

            if response.status_code == 200:
                return response.json()[0]

            if response.status_code == 503:
                estimated_time = response.json().get("estimated_time", 20)
                logger.info(
                    f"Model loading... waiting {estimated_time}s (Attempt {attempt + 1})"
                )
                time.sleep(estimated_time)
                continue

            response.raise_for_status()

        raise RuntimeError("HuggingFace model failed to load in time.")

    def get_emotion_features(self, audio_bytes: bytes) -> dict:
        """Calls an audio classification model to extract mood data on a 1-9 scale."""
        url = "https://api-inference.huggingface.co/models/amaai-lab/music2emo"

        # Base V/A Coordinates (Scale 1-9) for MTG-Jamendo style tags
        # We use these to calculate the final score if the API only returns tags
        VA_MAP = {
            "happy": (8.0, 7.0),
            "excited": (7.5, 8.5),
            "energetic": (7.0, 8.5),
            "dark": (3.0, 4.5),
            "sad": (2.0, 3.0),
            "melancholic": (3.5, 3.5),
            "slow": (5.0, 2.0),
            "deep": (4.5, 4.0),
            "calm": (6.5, 2.5),
            "aggressive": (2.5, 8.5),
            "intense": (4.0, 8.0),
            "epic": (6.5, 7.5),
        }

        for attempt in range(3):
            response = self.client.post(url, headers=self.headers, content=audio_bytes)

            if response.status_code == 200:
                predictions = response.json()

                # Scenario A: API natively returns V/A and Tags in a Dictionary
                # If your specific endpoint already calculates the 3.73 and 4.53 for you
                if isinstance(predictions, dict) and "valence" in predictions:
                    return {
                        "valence": float(predictions.get("valence", 5.0)),
                        "arousal": float(predictions.get("arousal", 5.0)),
                        "mood_tags": predictions.get(
                            "tags", []
                        ),  # Adjust key based on your JSON
                    }

                # Scenario B: API returns a standard HuggingFace list of dicts
                # [{"label": "dark", "score": 0.96}, {"label": "slow", "score": 0.88}, ...]
                if isinstance(predictions, list):
                    top_tags = []
                    total_weight = 0.0
                    weighted_v = 0.0
                    weighted_a = 0.0

                    for p in predictions:
                        label = p["label"].lower()
                        score = p["score"]

                        # Only keep highly confident tags
                        if score > 0.5:
                            top_tags.append(label)

                            # Calculate weighted V/A coordinates
                            if label in VA_MAP:
                                v, a = VA_MAP[label]
                                weighted_v += v * score
                                weighted_a += a * score
                                total_weight += score

                    # Normalize the coordinates
                    if total_weight > 0:
                        final_v = weighted_v / total_weight
                        final_a = weighted_a / total_weight
                    else:
                        # Neutral fallback
                        final_v, final_a = 5.0, 5.0

                    return {
                        "valence": round(max(1.0, min(9.0, final_v)), 2),
                        "arousal": round(max(1.0, min(9.0, final_a)), 2),
                        "mood_tags": top_tags[:5],  # Keep the top 5
                    }

            if response.status_code == 503:
                import time

                estimated_time = response.json().get("estimated_time", 15)
                logger.info(f"Emotion model loading... waiting {estimated_time}s")
                time.sleep(estimated_time)
                continue

            response.raise_for_status()

        # Fallback
        logger.warning("Emotion model failed. Returning neutral 1-9 coordinates.")
        return {"valence": 5.0, "arousal": 5.0, "mood_tags": ["unknown"]}
