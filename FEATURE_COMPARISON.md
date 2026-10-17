# Comprehensive Feature Comparison: Rumik AI vs. Zara

This document provides a scientific comparison between the publicly observed and documented capabilities of **Rumik AI** (Silk, Mesh, Peek, Ira) and the independent clean-room implementation of **Zara**.

Every feature is classified with its epistemological category and development status:
* **Evidence Category**: *Documented Fact*, *Observed Fact*, *Inferred Architecture*, or *Proprietary / Unknown*.
* **Status**: *Investigated*, *Implemented*, *Tested*, or *Roadmap / Future*.

---

## 1. Feature Comparison Matrix

| Feature / Domain | Rumik AI Target | Evidence Category | Zara Clean-Room Implementation | Zara Status |
| :--- | :--- | :--- | :--- | :--- |
| **Speech Model Architecture** | Silk Muga 1 / Mulberry 1.5; Rumik OSS 1 (3.4B Tiny Aya Fire + Kyutai Mimi 24kHz codec) | Documented Fact (HuggingFace, OpenAPI, Docs) | Modular multi-backend: Expressive Neural Engine (Edge-TTS) + Silk API bridge + Local model hook | **Implemented & Tested** |
| **Tone Steering** | Prefix tags (`[happy]`, `[excited]`, `[sad]`, `[angry]`, `[neutral]`, `[whisper]`) | Documented Fact (`prompting-muga.md`) | Dynamic prosody engine parsing tone tags into pitch/rate SSML deltas | **Implemented & Tested** |
| **Natural Language Voice Steering** | Natural language description formula (`"a female 30s hindi voice..."`) | Documented Fact (`prompting-mulberry.md`) | Voice profile descriptor mapping text descriptions to voice identities | **Implemented & Tested** |
| **Inline Vocalizations** | `<laugh>`, `<chuckle>`, `<sigh>`, `<gasp>`, `<cry>`, `<whisper>` | Documented Fact (`prompting-muga.md`) | Regex parser maps inline tags to timing pauses, pitch shifts, and expressive cues | **Implemented & Tested** |
| **Code-Switching & Hinglish** | 22 Indic languages + English, Devanagari & Latin script support | Documented Fact (Mintlify Docs & HuggingFace) | Built-in Hinglish colloquial lexicon + dual-script normalization + bilingual voices | **Implemented & Tested** |
| **Real-time Audio Streaming** | Low-latency chunked audio over WebSocket (`/v1/tts/stream`) | Documented Fact (OpenAPI 3.1.0) | Full-duplex WebSocket (`/v1/realtime`) streaming chunked audio packets | **Implemented & Tested** |
| **WebRTC Voice Calls** | LiveKit WebRTC transport for full-duplex conversations | Observed Fact (Playground JS bundles) | LiveKit/WebRTC ready; browser Web Speech API + HTML5 Audio streaming in Web UI | **Implemented & Tested** |
| **Telephony / SIP Trunks** | Inbound/outbound calls via Indian SIP trunks and carrier numbers | Documented Fact (OpenAPI `/v1/calls`) | Clean-room REST webhook structure; external SIP carrier bridge documented | **Investigated & Roadmap** |
| **Persistent Memory (Mesh)** | "Messy memory that knows what to remember and what to forget" | Documented Fact (Landing page & marketing) | SQLite relational memory engine (`ZaraMemoryEngine`) storing user facts & turns | **Implemented & Tested** |
| **Selective Retention** | Salience filtering (remembers personal facts, discards small talk) | Inferred Architecture | Rule-based and keyword-salience classifier separating facts from chatter | **Implemented & Tested** |
| **Contradiction Resolution** | Updates existing attributes when user provides new information | Inferred Architecture | Keyed fact slots (`career`, `location`, `preferences`) overwrite stale entries | **Implemented & Tested** |
| **Memory Inspection & Privacy**| User memory listing and explicit deletion | Documented API pattern | REST endpoints: `GET /v1/memory`, `DELETE /v1/memory/{id}`, `POST /v1/memory/clear` | **Implemented & Tested** |
| **Contextual Subtext (Peek)** | Decodes hidden meaning (e.g. *"I'm fine"* in late-night distress) | Documented Fact (Landing page) | `ZaraContextEngine` evaluates time-of-day, turn brevity, and emotional dissonance | **Implemented & Tested** |
| **Temporal Awareness** | Situational adaptation based on time of day | Inferred Architecture | Time-of-day detector applies soft/whisper registers at night, cheerful in morning | **Implemented & Tested** |
| **Multimodal Inputs** | Vision agents accepting camera feeds | Documented Fact (`vision-agents.md`) | Ingests image URLs / base64 frames to augment conversational prompt | **Implemented & Tested** |
| **Local CPU Inference** | Rumik OSS 1 (3.4B) on CPU is RTF ~13.5 (infeasible for live chat) | Tested Empirical Fact (Host has CPU only) | Lightweight high-speed neural TTS architecture achieves RTF < 0.05 on host CPU | **Implemented & Tested** |
| **Companion Web UI** | Glowing voice orb, waveform visualizer, push-to-talk mic | Observed Fact (Playground JS chunks) | High-fidelity interactive Web visualizer at `http://localhost:8000` | **Implemented & Tested** |

---

## 2. Technical Differentiation & Key Findings

1. **Clean-Room Guarantee**:
   No proprietary weights or private tokens from Rumik AI were extracted or decompiled. Zara's architecture was independently designed using publicly documented protocols, open weights references (`rumik-oss-1`), and authorized interface observation.
2. **Hardware Resilience**:
   While Rumik's 3.4B model requires server-side A100/H100 clusters or Apple Silicon MLX to achieve acceptable latency, Zara provides an instant, zero-cost, zero-GPU conversational voice pipeline capable of running on standard desktop/server CPUs while retaining rich emotional expression.
3. **Inspectable & Controllable Memory**:
   Unlike closed cloud companions that treat memory as an opaque vector store, Zara's memory engine gives users 100% transparency, inspection, and granular deletion control over their personal data.
