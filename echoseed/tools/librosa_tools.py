import librosa
import numpy as np
import io

# The DSP (Digital Signal Processing) layer
def extract_local_features(audio_bytes: bytes) -> dict:
    y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)

    # Energy (RMS)
    rms = librosa.feature.rms(y=y)
    energy = float(np.mean(rms))

    # Brightness (Spectral Centroid)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)
    brightness = float(np.mean(cent)) / (sr / 2) # normalize by Nyquist

    # Danceability (Variance of onset strength as a basic heuristic)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    danceability = float(np.var(onset_env))

    # Scale to 0.0 - 1.0 roughly
    return {
        "energy": min(1.0, energy * 10),
        "brightness": min(1.0, brightness),
        "danceability": min(1.0, danceability / 10)
    }