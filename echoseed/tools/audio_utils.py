import os
import io
import tempfile
import logging
import librosa
import soundfile as sf
import yt_dlp

logger = logging.getLogger("audio_utils")

<<<<<<< HEAD

# The Pre-processor - fetches the raw bytes from Spotify’s CDN.
def download_and_resample(preview_url: str, target_str: int = 16000) -> bytes:
    """Downloads an MP3 preview, saves it to disk temporarily, resamples it, and returns WAV bytes."""
=======
def fetch_true_segments(search_query: str, target_sr: int = 24000, segment_len: int = 15) -> tuple[bytes, bytes]:
    """
    Fetches full audio via yt-dlp, extracts the intro and outro as WAV bytes, and cleans up the source file.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(tempfile.gettempdir(), '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
>>>>>>> 6317959 (fix)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=True)
        if 'entries' in info:
            info = info['entries'][0]
        temp_file_path = ydl.prepare_filename(info)

    try:
        total_duration = librosa.get_duration(path=temp_file_path)
        
        intro_y, sr = librosa.load(temp_file_path, sr=target_sr, offset=0.0, duration=segment_len)
        
        outro_offset = max(0.0, total_duration - segment_len)
        outro_y, _ = librosa.load(temp_file_path, sr=target_sr, offset=outro_offset, duration=segment_len)

<<<<<<< HEAD
        # 4. Convert to a clean WAV byte-stream for HuggingFace
        wav_io = io.BytesIO()
        sf.write(wav_io, y, sr, format="WAV", subtype="PCM_16")
=======
        intro_io = io.BytesIO()
        sf.write(intro_io, intro_y, sr, format='WAV', subtype='PCM_16')
        
        outro_io = io.BytesIO()
        sf.write(outro_io, outro_y, sr, format='WAV', subtype='PCM_16')
>>>>>>> 6317959 (fix)

        return intro_io.getvalue(), outro_io.getvalue()

    except Exception as e:
        logger.error(f"Failed to process segments for {search_query}: {e}")
        raise

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)