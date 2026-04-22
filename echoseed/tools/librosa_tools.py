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
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    brightness = float(np.mean(centroid))

    # Danceability (Variance of onset strength as a basic heuristic)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    danceability = float(np.var(onset_env))

    #Calculate BPM (Tempo)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    # librosa 0.10+ returns tempo as a 1D array, so we extract the float
    bpm = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)

    # Scale to 0.0 - 1.0 roughly
    return {
        "energy": energy,
        "brightness": brightness,
        "danceability": danceability,
        "bpm": bpm
    }