# 🌱 EchoSeed

EchoSeed is an agentic, distributed audio intelligence system that blends Digital Signal Processing (DSP), Deep Learning, and LLM orchestration to curate playlists that don't just match metadata, but match the actual **"Music DNA"** of your library.

Unlike traditional generators, EchoSeed uses a distributed worker-orchestrator model to perform high-compute inference on raw audio previews, extracting 768-dimensional embeddings to find the perfect sonic vibe.

---

## 🏗️ Distributed Architecture

EchoSeed decouples Spotify orchestration from heavy AI compute:

- **Orchestrator (AWS T3)** — Runs the LangGraph engine, handles Spotify OAuth, manages the user CLI, and coordinates the analysis pipeline.
- **AI Worker (AWS M7i)** — A high-performance FastAPI server that loads MERT-v1 into memory to perform raw audio inference, BPM detection, and spectral analysis.

---

## 🚀 Key Features

- **Agentic Workflows** — Powered by LangGraph, the system treats playlist generation as a multi-stage reasoning task: fetching, analyzing, clustering, and validating.
- **Deep Audio DNA** — Uses MERT-v1 (95M parameter model) from HuggingFace to generate high-fidelity audio embeddings.
- **DSP Analysis** — Real-time extraction of BPM, spectral centroid (brightness), and onset strength (danceability) via Librosa.
- **Distributed Inference** — Offloads heavy PyTorch tensors to a dedicated compute worker to maintain low-latency on the main app.
- **LangSmith Tracing** — Full observability into the agentic decision-making process and inference latency.
- **Smart Refresh** — A robust network monitor that automatically recovers from drops and refreshes Spotify tokens securely.

---

## 🛠️ Tech Stack

**Core Orchestration**
- [LangGraph](https://langchain-ai.github.io/langgraph/) – Agentic state management
- [Spotipy](https://spotipy.readthedocs.io/) – Spotify Web API
- [Cryptography](https://cryptography.io/) – AES token encryption

**AI & Signal Processing**
- [PyTorch](https://pytorch.org/) – Deep Learning backend
- [MERT-v1](https://huggingface.co/m-a-p/MERT-v1-95M) – Music Encoder for Representation and Tracking
- [Librosa](https://librosa.org/) – Audio and music processing
- [FastAPI](https://fastapi.tiangolo.com/) – High-performance worker API

**Infrastructure**
- AWS EC2 (M7i-flex for compute, T3 for orchestration)
- systemd – Linux daemon management
- zsh – Primary development environment

---

## ⚩ Quick Start

### 1. Deployment

EchoSeed uses two branches depending on the environment:

| Branch | Deploy on |
|--------|-----------|
| `main` | Orchestrator (T3) |
| `worker` | AI Worker (M7i) |

### 2. Configure Environment (`.env`)

```bash
# General
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SECRET_KEY=...

# AI Configuration
GEMINI_API_KEY=...
LANGCHAIN_API_KEY=...
LANGCHAIN_TRACING_V2=true

# Distributed Networking
WORKER_URL=http://<m7i-private-ip>:8000/analyze
```

### 3. Initialize the Worker (M7i)

The worker requires a specialised environment to handle the OOM demands of audio models:

```bash
# Enable 4GB swap for MERT inference
sudo fallocate -l 4G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile

# Start the FastAPI worker
sudo systemctl enable echoseed-ai
sudo systemctl start echoseed-ai
```

### 4. Run the Pipeline (T3)

```bash
python main.py
```

---

## 🧠 The Math Behind the Vibe

EchoSeed finds similarities by calculating **Cosine Similarity** between track embeddings in a 768-dimensional space:

$$\text{similarity} = \frac{A \cdot B}{\|A\| \|B\|}$$

Where `A` is your seed track and `B` is a candidate from your library. This allows EchoSeed to find tracks that *sound* alike — even across completely different genres.

---

## 📂 Project Structure

```
echoseed/
├── api/         # Spotify auth & playlist services
├── graph/       # LangGraph state & node definitions
├── ai/          # Clustering logic & preprocessing
├── security/    # Token encryption & network monitoring
├── ui/          # CLI menu system
├── state/       # TypedDict schemas for LangGraph
main.py          # System entry point
worker.py        # FastAPI worker (worker branch)
```

---

## 📜 License

MIT License © 2026 Isaiah Juma
