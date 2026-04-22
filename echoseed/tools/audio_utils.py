import httpx
import librosa
import soundfile as sf
import tempfile
import io
import os
import logging

logger = logging.getLogger("audio_utils")

# The Pre-processor - fetches the raw bytes from Spotify’s CDN.
def download_and_resample(preview_url: str, target_str: int = 16000) -> bytes:
    """Downloads an MP3 preview, saves it to disk temporarily, resamples it, and returns WAV bytes."""

    # 1. Download the raw data
    # follow_redirects is crucial because audio CDNs often redirect URLs
    with httpx.Client(follow_redirects=True) as client:
        response = client.get(preview_url)
        response.raise_for_status()

    # 2. Write to a temporary file on disk so librosa's MP3 decoder can read it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_file.write(response.content)
        tmp_path = tmp_file.name

    try:
        # 3. Load from disk and resample
        # This is where librosa calls ffmpeg behind the scenes
        y, sr = librosa.load(tmp_path, sr=target_str)

        # 4. Convert to a clean WAV byte-stream for HuggingFace
        wav_io = io.BytesIO()
        sf.write(wav_io, y, sr, format='WAV', subtype='PCM_16')

        return wav_io.getvalue()

    except Exception as e:
        logger.error(f"Failed to process audio data: {e}")
        raise

    finally:
        # 5. Always clean up the temp file, even if it crashes
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
