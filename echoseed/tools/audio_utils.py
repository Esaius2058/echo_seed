import httpx
import librosa
import soundfiles as sf
import io

# The Pre-processor - fetches the raw bytes from Spotify’s CDN.
def download_and_resample(preview_url: str, target_str: int = 16000) -> bytes:
    response = httpx.get(preview_url)
    response.raise_for_status()

    # load audio from memory into librosa
    # it mathematically interpolates the audio to exactly 16,000 samples per second
    y, sr = librosa.load(io.BytesIO(response.content), sr=target_str)

    # convert back to wav bytes
    wav_io = io.BytesIO()
    sf.write(wav_io, y, target_str, format='WAV', subtype='PCM_16')
    return wav_io.getvalue()
