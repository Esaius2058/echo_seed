# 🌱 EchoSeed

EchoSeed is an AI-powered virtual DJ, one that actually listens to your music before building your playlist.
Most playlist tools look at labels: genre, artist, release date. EchoSeed goes deeper. It listens to the raw audio of each song and breaks it down the same way a sound engineer would; the tempo, the energy, the emotional tone, the brightness of the mix, how hard the beat hits. Every song gets its own sonic fingerprint.

From there, EchoSeed arranges your playlist so that each song flows naturally into the next: matching energy levels, complementing keys, and easing the mood from one track to another. So there are no jarring jumps, no awkward silences, no tonal whiplash. Just a seamless listen, start to finish.

The result sounds like a set built by a professional DJ who spent hours hand-picking and sequencing every track. Except it took seconds.

---

## 🏗️ Distributed Architecture

EchoSeed decouples Spotify orchestration from heavy AI compute:

- **Orchestrator (AWS t3)** — Runs the LangGraph engine, handles Spotify OAuth, manages the user CLI, and coordinates the analysis pipeline.
- **AI Worker (AWS m7i)** — A high-performance FastAPI server that loads MERT-v1 into memory to perform raw audio inference, BPM detection, and spectral analysis.

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
- AWS EC2 (m7i-flex for compute, t3 for orchestration)
- systemd – Linux daemon management
- zsh – Primary development environment

---

## ⚩ Quick Start

### 1. Deployment

EchoSeed uses two branches depending on the environment:

| Branch | Deploy on |
|--------|-----------|
| `main` | Orchestrator (t3) |
| `worker` | AI Worker (m7i) |

#### Branch Logic
| Component | `main` Branch purpose | `worker` Branch purpose |
|--------|---------------|---------------|
| `main.py` | Initializes the CLI and triggers the LangGraph workflow. | Spins up a FastAPI server to listen for audio bytes. |
| Data Flow | Streams raw audio bytes to the worker. | Receives bytes and returns BPM + 768D Embeddings. |
| Dependencies | LangChain, Spotipy, Cryptography. | Cryptography.	PyTorch, Transformers, Librosa, Uvicorn. |

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

### 3. Initialize the Worker (m7i)

The worker requires a specialised environment to handle the OOM demands of audio models:

```bash
# Enable 4GB swap for MERT inference
sudo fallocate -l 4G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile

# Start the FastAPI worker
sudo systemctl enable echoseed-ai
sudo systemctl start echoseed-ai
```

### 4. Run the Pipeline (t3)

```bash
python main.py
```

---

## 🧠 The Math Behind the Vibe

EchoSeed finds similarities by calculating **Cosine Similarity** between track embeddings in a 768-dimensional space:

$$\text{similarity} = \frac{A \cdot B}{\|A\| \|B\|}$$

Where `A` is your seed track and `B` is a candidate from your library. This allows EchoSeed to find tracks that *sound* alike, even across completely different genres.

---

## 📂 Project Structure
### Main Branch (The Orchestrator)
**Target:** aws t3 instance
**Role:** State management, Spotify API coordination, and LangGraph execution.

```
echoseed/
├── api/         # Spotify auth & playlist services
├── graph/       # LangGraph state & node definitions
├── security/    # Token encryption & network monitoring
├── ui/          # CLI menu system
├── state/       # TypedDict schemas for LangGraph
├── main.py        # Orchestrator Entry Point (Invokes LangGraph)
```

### Worker Branch (The AI Inference Engine)
**Target:** AWS m7i-flex Instance
**Role:** High-compute DSP analysis and MERT model inference.

```
echoseed/
├── ai/              # Signal processing & Librosa wrappers
├── models/          # Local MERT model cache (~400MB)
└── main.py          # Worker Entry Point (FastAPI /analyze endpoint)
```
---



## 📜 License

MIT License © 2026 Isaiah Juma