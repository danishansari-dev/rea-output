# Zara: System Architecture & Engineering Blueprint

## 1. High-Level Blueprint

**Zara** is an independently designed, modular, emotionally intelligent AI companion and voice platform inspired by Rumik AI's Silk, Mesh, and Peek systems.

Zara decouples conversation reasoning, voice generation, long-term memory, and contextual intelligence into four independently testable, swappable components:

```
                            ┌──────────────────────────────────────┐
                            │      Client Applications             │
                            │  (Browser Web UI / Mobile / WebRTC)  │
                            └──────────────────┬───────────────────┘
                                               │
                                  HTTP REST / WebSocket Audio
                                               │
                                               ▼
     ┌──────────────────────────────────────────────────────────────────────────────────┐
     │                             Zara FastAPI Server                                  │
     │     - /v1/tts (Silk TTS API)                 - /v1/realtime (Streaming WS)       │
     │     - /v1/agents/chat (Companion Dialogue)   - /v1/memory (Mesh Memory API)      │
     └─────────────────────────────────────────┬────────────────────────────────────────┘
                                               │
         ┌──────────────────┬──────────────────┼──────────────────┬──────────────────┐
         ▼                  ▼                  ▼                  ▼                  ▼
┌──────────────────┐┌──────────────────┐┌──────────────────┐┌──────────────────┐┌──────────────────┐
│   Conversation   ││ Expressive Voice ││  Memory Engine   ││  Context Engine  ││ Web Visualizer   │
│      Engine      ││      Engine      ││ (Mesh Equivalent)││ (Peek Equivalent)││    Playground    │
├──────────────────┤├──────────────────┤├──────────────────┤├──────────────────┤├──────────────────┤
│ - Dialogue State ││ - Multi-Backend  ││ - SQLite Store   ││ - Subtext Decode ││ - Reactive Orb   │
│ - Persona Prompt ││ - SSML Prosody   ││ - Selective Facts││ - Hinglish Lex.  ││ - Audio Waveform │
│ - Pluggable LLM  ││ - Tone Tag Parse ││ - Contradictions ││ - Temporal Cues  ││ - Push-To-Talk   │
│ - Graceful Fallbk││ - Chunks Stream  ││ - User Deletion  ││ - Multimodal In  ││ - Memory Admin   │
└──────────────────┘└──────────────────┘└──────────────────┘└──────────────────┘└──────────────────┘
```

---

## 2. Component Specifications

### 2.1. Conversation Engine (`ZaraConversationEngine`)
* **Role**: Manages multi-turn conversation history, applies the Zara companion persona, orchestrates memory and context inputs, and generates conversational text formatted for speech.
* **Pluggable Model Architecture**:
  - Direct connection to cloud LLM providers (OpenAI GPT-4o-mini, Gemini, Anthropic) if an API key is provided via environment variables.
  - Robust offline heuristic/neural fallback companion generator ensuring Zara operates seamlessly with zero cloud dependencies or zero API spend.
* **Persona Guardrails**:
  - Warm, caring, conversational tone (1 to 3 sentences per turn, optimized for speech).
  - Emits natural inline emotion tags (`[whisper]`, `[happy]`, `<laugh>`, `<sigh>`).

### 2.2. Expressive Voice Engine (`ZaraVoiceEngine`)
* **Role**: Synthesizes expressive, natural audio from text.
* **Multi-Backend Architecture**:
  1. *Neural Prosody Backend (Default)*: High-speed, zero-cost edge neural engine modulating pitch, rate, and contour based on bracketed tone tags and emotional states. Runs on any CPU with $<200\text{ ms}$ streaming latency.
  2. *Silk API Bridge*: Forwards requests to Rumik's `POST /v1/tts` endpoint if `RUMIK_API_KEY` is configured.
  3. *Local Model Bridge*: Extensible loader for `rumik-oss-1` or `Kokoro` when CUDA/MLX accelerators are available.
* **Streaming Protocol**: Yields raw chunked audio packets through an asynchronous generator for real-time WebSocket transmission.

### 2.3. Memory Engine (`ZaraMemoryEngine` — Mesh Equivalent)
* **Role**: Solves persistent companion memory without token bloat or context corruption.
* **Database Backend**: Thread-safe SQLite database (`zara_memory.db`) with WAL mode.
* **Schema**:
  - `user_facts`: Keyed personal attributes (`key`, `category`, `fact_value`, `salience_score`, `created_at`, `updated_at`).
  - `conversation_turns`: Full history with message timestamps, detected sentiments, and session tokens.
* **Key Features**:
  - *Selective Fact Extraction*: Evaluates incoming text for self-disclosures (e.g. name, location, family, career, emotional triggers).
  - *Contradiction Resolution*: Updates existing category slots when the user shares new information.
  - *Semantic Recall*: Retrieves the top relevant user facts for injection into the prompt.
  - *Privacy & Deletion*: Exposes complete CRUD endpoints (`GET /v1/memory`, `DELETE /v1/memory/{id}`, `POST /v1/memory/clear`).

### 2.4. Context Engine (`ZaraContextEngine` — Peek Equivalent)
* **Role**: Analyzes situational signals, cultural nuance, and emotional subtext.
* **Features**:
  - *Temporal Resolver*: Computes local time-of-day (e.g. late night vs morning) to adjust companion empathy and vocal energy.
  - *Hinglish & Regional Normalizer*: Recognizes and translates colloquial Hindi-English expressions (*"yaar"*, *"bilkul"*, *"tension"*, *"kya chal raha hai"*).
  - *Subtext Decoder*: Detects when brevity or curt punctuation signifies suppressed distress (e.g. decoding *"I'm fine."*).
  - *Multimodal Ingestion*: Attaches visual context to the conversation if image data is supplied.

---

## 3. API Contract & Data Protocols

### REST Endpoints
* `POST /v1/tts`: Synthesize speech (supports `model`, `text`, `voice`, `emotion`, `audio_format`). Returns audio bytes or JSON.
* `POST /v1/agents/chat`: Send a companion message; returns text reply, mood, decoded intent, and base64 audio.
* `GET /v1/voices`: Discover available voice personalities and their linguistic configurations.
* `GET /v1/memory`: List stored long-term user facts and memories.
* `DELETE /v1/memory/{fact_id}`: Delete a specific memory item.
* `POST /v1/memory/clear`: Erase all user memory (GDPR right-to-be-forgotten).

### WebSocket Full-Duplex Real-Time Session
* `WS /v1/realtime`:
  - Client sends JSON: `{"action": "chat", "text": "Hey Zara!", "voice": "zara-expressive"}`
  - Server streams text metadata event: `{"event": "text_reply", "text": "...", "mood": "..."}`
  - Server streams binary audio packets chunk-by-chunk in real time.
  - Server signals completion: `{"event": "stream_end"}`
