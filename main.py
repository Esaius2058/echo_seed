import os
import io
import gc
import torch
import librosa
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from transformers import AutoModel, Wav2Vec2FeatureExtractor
from dotenv import load_dotenv

# Optimization: Limit threads to save memory on the m7i
torch.set_num_threads(1)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("echoseed.worker")

app = FastAPI(title="EchoSeed AI Worker")

# Absolute paths for standalone models
MODELS_BASE = os.path.expanduser("~/models")
MERT_PATH = os.path.join(MODELS_BASE, "mert")

logger.info("[EchoSeed] Loading AI Models...")
try:
    mert_model = AutoModel.from_pretrained(
        "m-a-p/MERT-v1-95M", 
        cache_dir=MERT_PATH, 
        trust_remote_code=True,
        return_dict=True
    )
    mert_ext = Wav2Vec2FeatureExtractor.from_pretrained("m-a-p/MERT-v1-95M", cache_dir=MERT_PATH)
    logger.info("[EchoSeed] Models Loaded Successfully")
except Exception as e:
    logger.error(f"Model Loading Failed: {e}")

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        # 1. Read bytes and immediately load into librosa
        audio_bytes = await file.read()
        y, sr = librosa.load(io.BytesIO(audio_bytes), sr=24000)
        del audio_bytes 
        
        # 2. Tempo Logic
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
        
        # 3. MERT Inference
        with torch.no_grad():
            inputs = mert_ext(y, sampling_rate=sr, return_tensors="pt")
            outputs = mert_model(**inputs)
            embedding = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
        
        # 4. Explicit Cleanup
        del y, inputs, outputs
        gc.collect() 
        
        return {
            "status": "success",
            "bpm": round(bpm, 2),
            "embedding": embedding
        }
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
