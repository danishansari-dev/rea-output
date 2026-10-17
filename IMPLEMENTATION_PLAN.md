# Zara: Implementation Roadmap & Execution Plan

## 1. Overview & Strategy

This document outlines the systematic, phased execution plan to build **Zara** as a modular AI companion inspired by Rumik AI's Silk, Mesh, and Peek architectures.

---

## 2. Execution Phases

### Phase 1: Reconnaissance & Target Investigation (Completed)
* [x] Inspect existing workspace files, scripts, and downloaded Rumik HTML/JS artifacts.
* [x] Reverse-engineer OpenAPI schemas for Silk TTS and Voice Agent APIs.
* [x] Extract Muga and Mulberry prompt engineering rules, tone tags, and inline events.
* [x] Identify open-weights model `rumik-ai/rumik-oss-1` (Tiny Aya Fire 3.4B + Kyutai Mimi 24kHz codec).
* [x] Perform hardware benchmark: host has PyTorch CPU only, no CUDA GPU (precluding real-time 3.4B autoregressive local inference).
* [x] Author technical research documents (`RIA_CAPABILITIES.md`, `RUMIK_ARCHITECTURE.md`, `SILK_VOICE_RESEARCH.md`, `MESH_MEMORY_RESEARCH.md`, `PEEK_CONTEXT_RESEARCH.md`, `FEATURE_COMPARISON.md`, `VOICE_TRAINING_PLAN.md`, `ZARA_ARCHITECTURE.md`).

### Phase 2: Engine Implementation & Modularity (In Progress)
* [ ] **Memory Engine (`zara/memory_engine.py`)**:
  - Implement SQLite store (`zara_memory.db`) with `user_facts` and `conversation_turns`.
  - Build selective fact extractor (recognizes name, location, family, career, emotional triggers).
  - Implement contradiction resolution (updates existing key slots instead of duplicating).
  - Implement memory retrieval with relevance ranking.
  - Implement inspection and deletion methods.
* [ ] **Context Engine (`zara/context_engine.py`)**:
  - Implement temporal resolver (detects time-of-day and attaches situational advice).
  - Implement Hinglish and informal language normalizer and dictionary.
  - Implement subtext and emotional intent analyzer (decodes hidden distress, e.g. *"I'm fine"*).
  - Implement multimodal context handler (attaches image metadata).
* [ ] **Expressive Voice Engine (`zara/voice_engine.py`)**:
  - Support tone tags (`[happy]`, `[excited]`, `[sad]`, `[angry]`, `[neutral]`, `[whisper]`).
  - Support inline event tags (`<laugh>`, `<chuckle>`, `<sigh>`).
  - Multi-backend support: Edge-TTS Neural prosody (default), Silk API bridge, and Local model hook.
  - Asynchronous chunked streaming generator for real-time WebSocket playback.
* [ ] **Conversation Engine (`zara/conversation_engine.py`)**:
  - Unify Memory, Context, and Persona into clean prompt assembly.
  - Pluggable LLM support (OpenAI, Gemini) with robust offline heuristic fallback.
  - Generates voice-ready dialogue turns (1 to 3 sentences).

### Phase 3: Server Integration & API Exposure
* [ ] Expose updated endpoints in `zara/server.py`:
  - `POST /v1/tts` (Silk TTS compatible)
  - `POST /v1/agents/chat` (Context- and memory-aware chat)
  - `GET /v1/memory` (List remembered facts)
  - `DELETE /v1/memory/{id}` (Delete memory item)
  - `POST /v1/memory/clear` (Clear all memories)
  - `WS /v1/realtime` (Streaming audio and text events)

### Phase 4: UI & Playground Enhancements
* [ ] Update `zara/static/index.html`:
  - Interactive glowing voice orb with audio waveform canvas.
  - Memory inspector panel showing live extracted facts from the conversation.
  - Voice selector with Hinglish, Expressive, Intimate, and Playful options.
  - Microphone push-to-talk integration.

### Phase 5: Verification & Testing
* [ ] Run automated integration tests verifying:
  - Memory persistence, fact updates, and contradiction handling.
  - Context engine subtext decoding and Hinglish processing.
  - Voice engine prosody modulation and audio chunk streaming.
  - API endpoints and error recovery.

### Phase 6: Final Documentation & Git Delivery
* [ ] Update `PROGRESS.md` and `README.md`.
* [ ] Format Git commands adhering strictly to the user's global rule.
