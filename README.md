# Zara — Emotionally Intelligent Voice AI Platform & Companion

**Zara** is an independent, modular, clean-room AI companion and expressive voice platform inspired by Rumik AI's **Silk** (Voice), **Mesh** (Memory), **Peek** (Context Understanding), and **Ira** (Companion).

---

## Architecture Overview

```
                           [ Browser / Mobile / WebRTC Client ]
                                            │
                               ┌────────────┴────────────┐
                               ▼                         ▼
                      [ Web UI & Visualizer ]   [ Push-to-Talk Mic ]
                               │                         │
                               └────────────┬────────────┘
                                            ▼
                                  [ Zara FastAPI Server ]
            (/v1/tts, /v1/agents/chat, /v1/realtime, /v1/memory, /v1/context)
                                            │
       ┌──────────────────────┬─────────────┴─────────────┬──────────────────────┐
       ▼                      ▼                           ▼                      ▼
[ Conversation Engine ] [ Expressive Voice ]      [ Memory Engine ]      [ Context Engine ]
  (Zara Brain)            (Silk Equivalent)         (Mesh Equivalent)      (Peek Equivalent)
- Dialogue State        - Multi-Backend TTS       - Persistent SQLite    - Subtext Decoder
- Persona Guardrails    - Muga Tone Tags          - Selective Retention  - Hinglish Lexicon
- Pluggable LLM         - Inline Paralinguistics  - Contradiction Update - Temporal Cues
- Fallback Generator    - Low-Latency Streaming   - User Deletion & CRUD - Multimodal Ingestion
```

---

## Core Pillars & Capabilities

1. **Silk-Grade Expressive Neural Speech (`POST /v1/tts`, `WS /v1/realtime`)**:
   - Supports Muga-style tone steering (`[happy]`, `[whisper]`, `[sad]`, `[angry]`, `[neutral]`, `[excited]`).
   - Dynamic prosody modulation for paralinguistic events (`<laugh>`, `<chuckle>`, `<sigh>`).
   - Six built-in voice personalities: `zara-expressive`, `zara-hinglish`, `zara-intimate`, `zara-playful`, `zara-storyteller`, `zara-podcast`.
   - Asynchronous chunked audio streaming over WebSockets for $< 200\text{ms}$ time-to-first-byte.

2. **Mesh Persistent Memory Engine (`GET /v1/memory`, `DELETE /v1/memory/{id}`)**:
   - Thread-safe SQLite store (`zara_memory.db`) with WAL mode.
   - Selective fact extraction (identity, career, location, preferences, emotional stressors).
   - Contradiction resolution: updating facts (e.g. city or job) cleanly overwrites old beliefs without duplication.
   - User-controlled memory inspection and deletion for privacy compliance (GDPR right-to-be-forgotten).

3. **Peek Context & Cultural Intelligence (`POST /v1/context/analyze`)**:
   - Subtext decoding: discerns when surface phrases (e.g. *"I'm fine."* at 2:30 AM) signal emotional distress or vulnerability.
   - Hinglish and Indic code-switching: parses colloquial discourse markers (*"yaar"*, *"arre"*, *"bilkul"*, *"pakka"*).
   - Temporal awareness: adjusts companion demeanor based on local time (late-night intimate whisper vs morning cheerfulness).

4. **Interactive Web Visualizer & Playground (`http://localhost:8000`)**:
   - Glowing reactive voice orb that pulsates dynamically while listening and speaking.
   - Real-time HTML5 audio waveform canvas.
   - In-browser speech recognition (Web Speech API) for hands-free voice interaction.
   - Mesh Memory Inspector drawer allowing users to view and delete remembered facts in real time.

---

## Research & Documentation Artifacts

Detailed reverse-engineering findings and technical reports are stored directly in the workspace:
* [`RIA_CAPABILITIES.md`](file:///d:/Code%20Playground/rea-output/RIA_CAPABILITIES.md): RIA's 207 MCP tools and investigation protocols.
* [`RUMIK_ARCHITECTURE.md`](file:///d:/Code%20Playground/rea-output/RUMIK_ARCHITECTURE.md): Ecosystem blueprint of Rumik AI, Silk, Mesh, Peek, and Ira.
* [`SILK_VOICE_RESEARCH.md`](file:///d:/Code%20Playground/rea-output/SILK_VOICE_RESEARCH.md): Detailed analysis of Tiny Aya Fire, Kyutai Mimi 24kHz codec, and CPU/GPU benchmarks.
* [`MESH_MEMORY_RESEARCH.md`](file:///d:/Code%20Playground/rea-output/MESH_MEMORY_RESEARCH.md): Cognitive memory modeling, selective retention, and contradiction handling.
* [`PEEK_CONTEXT_RESEARCH.md`](file:///d:/Code%20Playground/rea-output/PEEK_CONTEXT_RESEARCH.md): Subtext decoding, Hinglish parsing, and situational awareness.
* [`FEATURE_COMPARISON.md`](file:///d:/Code%20Playground/rea-output/FEATURE_COMPARISON.md): Matrix comparing Rumik AI target vs Zara implementation with evidence classifications.
* [`VOICE_TRAINING_PLAN.md`](file:///d:/Code%20Playground/rea-output/VOICE_TRAINING_PLAN.md): Dataset licensing, compute feasibility, and small LoRA pilot training plan.
* [`ZARA_ARCHITECTURE.md`](file:///d:/Code%20Playground/rea-output/ZARA_ARCHITECTURE.md): System architecture of Zara's four decoupled engines.
* [`IMPLEMENTATION_PLAN.md`](file:///d:/Code%20Playground/rea-output/IMPLEMENTATION_PLAN.md): Step-by-step roadmap and verification protocol.
* [`PROGRESS.md`](file:///d:/Code%20Playground/rea-output/PROGRESS.md): Live progress tracker and test results.

---

## Quick Start

```bash
# 1. Install dependencies
pip install fastapi uvicorn edge-tts websockets pytest

# 2. Run the test suite
python tests/test_zara.py
python tests/test_server_api.py

# 3. Launch Zara
python run_zara.py
```

Open your browser at **`http://localhost:8000`** to interact with Zara.
