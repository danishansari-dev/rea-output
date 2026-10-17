# Rumik AI Architectural Analysis & System Blueprint

## 1. System Overview

**Rumik AI** (rumik.ai) is an artificial intelligence research laboratory focused on building emotionally intelligent, conversational voice and multimodal systems with a strong emphasis on English and Indic languages (22 scheduled Indian languages plus English).

The platform is organized around three proprietary core pillars and one flagship consumer application:

```
                           ┌──────────────────────────────────────────────┐
                           │          Rumik AI Ecosystem Architecture     │
                           └──────────────────────┬───────────────────────┘
                                                  │
                ┌─────────────────────────────────┼─────────────────────────────────┐
                ▼                                 ▼                                 ▼
   ┌─────────────────────────┐       ┌─────────────────────────┐       ┌─────────────────────────┐
   │       SILK (Voice)      │       │      MESH (Memory)      │       │      PEEK (Context)     │
   │ - Silk Muga 1           │       │ - Selective retention   │       │ - Nuance & subtext      │
   │ - Silk Mulberry 1.5     │       │ - Fact contradiction    │       │ - Hinglish decoding     │
   │ - Rumik OSS 1 (3.4B)    │       │ - Dynamic forgetting    │       │ - Temporal cues         │
   │ - Kyutai Mimi 24kHz     │       │ - Semantic recall       │       │ - Multimodal intent     │
   └────────────┬────────────┘       └────────────┬────────────┘       └────────────┬────────────┘
                │                                 │                                 │
                └─────────────────────────────────┼─────────────────────────────────┘
                                                  │
                                                  ▼
                               ┌─────────────────────────────────────┐
                               │           IRA (Companion)           │
                               │ - Emotionally resonant voice agent  │
                               │ - Real-time full-duplex dialogue    │
                               │ - LiveKit WebRTC / WebSocket audio  │
                               └─────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1. Silk: Neural Speech Generation
Silk is Rumik's voice synthesis engine, delivering expressive, code-switched, and low-latency speech.
* **Silk Muga 1**: Steered by explicit bracketed tone tags at the beginning of each paragraph (`[happy]`, `[excited]`, `[sad]`, `[angry]`, `[neutral]`, `[whisper]`) and inline vocalization events (`<laugh>`, `<chuckle>`, `<sigh>`). Requires buffering the complete tagged sentence before synthesis.
* **Silk Mulberry 1.5**: Steered by natural-language descriptive prompts (e.g. *"a female 30s hindi voice, smooth timbre, conversational pacing, casual register, like a podcast host"*). Supports twelve preset speaker embeddings (`emma`, `mia`, `sophia`, `ava`, `ira`, `siya`, `aisha`, `zoya`, `lucas`, `noah`, `theo`, `adam`). Supports rich inline events (`<laugh>`, `<sigh>`, `<gasp>`, `<cry>`, `<whisper>`). Capable of streaming audio chunks while generating.
* **Rumik OSS 1 (Open Weights)**: 3.4B parameter causal transformer model based on `CohereLabs/tiny-aya-fire` using Kyutai's Mimi neural audio codec (interleaved acoustic and semantic tokens, 8 codebook tokens per frame).

### 2.2. Mesh: Memory Architecture
Mesh addresses the challenge of persistent companion memory. Rather than acting as a static vector dump of all past chat logs, Mesh mimics human cognitive memory:
* **Selective Retention**: Distinguishes ephemeral small-talk (e.g., *"it's raining outside"*) from durable personal attributes (e.g., *"my sister is a doctor"* or *"I get anxious before interviews"*).
* **Contradiction Resolution & State Updates**: When the user provides updated facts (e.g., *"I moved from Mumbai to Bengaluru"*), Mesh updates or invalidates outdated entries rather than retrieving contradictory memories.
* **Decay & Pruning**: Low-salience interactions decay over time, preventing context window bloat and irrelevant retrieval.
* **Controlled Access**: Provides programmatic inspection and user-facing deletion for privacy compliance.

### 2.3. Peek: Contextual & Cultural Understanding
Peek is Rumik's contextual intelligence engine, designed to decode emotional subtext, temporal awareness, and linguistic nuances:
* **Subtext Decoding**: Distinguishes surface text from true sentiment (e.g., recognizing that *"I'm fine."* sent at 2:00 AM carries sadness or distress compared to a midday confirmation).
* **Hinglish & Regional Code-Switching**: Natively parses colloquial Indian conversational language, blending Devanagari and Latin scripts, slang (*"yaar"*, *"jugaad"*, *"pakka"*, *"scene kya hai"*), and grammatical code-switching.
* **Multimodal Grounding**: Evaluates conversational cues alongside situational signals (camera input in vision agents, time-of-day, audio prosody in voice input).

### 2.4. Ira: Conversational Companion
Ira is the consumer manifestation combining Silk, Mesh, and Peek into an AI friend and empathetic listener.
* Interacts over real-time voice with natural turn-taking.
* Expresses warmth, humor, and empathetic active listening.
* Maintains emotional state transitions across conversation turns.

---

## 3. Communication Protocols & Infrastructure

Through Ria bundle inspection and OpenAPI schema analysis, Rumik's delivery infrastructure was verified:

| Layer | Technology | Observed Behavior |
| :--- | :--- | :--- |
| **REST API** | FastAPI / Starlette (`https://silk-api.rumik.ai/v1/tts`) | Accepts JSON payloads, returns binary audio (`wav`, `opus`, `pcm`, `mp3`, `mulaw`, `alaw`) with custom headers `X-Audio-Duration-Ms` and `X-Usage-Cost-Nanos`. |
| **Streaming WS** | WebSocket (`/v1/tts/stream`) | Accepts JSON frame with text/voice, streams chunked raw 24kHz PCM or Opus packets. |
| **Realtime Agent** | LiveKit WebRTC Transport & SIP Trunks | Full-duplex audio stream via LiveKit Cloud/Server; integrates with telephone networks (+91 numbers) via SIP. |
| **Frontend UI** | Next.js 14 App Router & Framer | Interactive Playground with live waveform audio nodes, agent configuration panels, and token analytics. |
| **Telemetry & Auth**| Firebase Auth, PostHog, Sentry | User session tokens, event telemetry, and rate-limiting enforcement. |

---

## 4. Evidence Classification Table

| Component | Status | Supporting Evidence | Confidence |
| :--- | :--- | :--- | :--- |
| **Silk TTS API (`/v1/tts`)** | **Documented Fact** | OpenAPI 3.1.0 specification at `docs.rumik.ai`, confirmed curl examples, endpoint responses. | High (100%) |
| **Silk Muga Prompting** | **Documented Fact** | Official `prompting-muga.md` documentation, ToneMatrix specification, sample audio files. | High (100%) |
| **Silk Mulberry Prompting**| **Documented Fact** | Official `prompting-mulberry.md` documentation, description formula, preset speaker list. | High (100%) |
| **Rumik OSS 1 Model Weights**| **Documented Fact** | Hugging Face repository `rumik-ai/rumik-oss-1`, `tiny-aya-fire` backbone, Kyutai Mimi codec. | High (100%) |
| **Mesh Memory Logic** | **Documented / Inferred**| Public descriptions on landing page ("messy memory that knows what to remember"), patent/architectural descriptions. | Medium (80%) |
| **Peek Context Logic** | **Documented / Inferred**| Public descriptions ("understands 'i'm fine' in every context"), Hinglish normalization docs. | Medium (80%) |
| **LiveKit WebRTC Transport** | **Observed Fact** | Extracted from Next.js playground JavaScript bundles in `playground_app/` (imports `@livekit/components-react`). | High (100%) |
| **Proprietary Weights for Muga**| **Unknown / Private** | Cloud endpoints only; exact server-side checkpoint weights are proprietary and not published. | Complete Unknown |
