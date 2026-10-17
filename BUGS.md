# Zara Defect Tracking Ledger (BUGS.md)

This ledger tracks all discovered defects, security vulnerabilities, edge-case failures, and architectural regressions in Zara, along with root cause analyses, applied remediations, and empirical verification test outcomes.

---

## Defect Summary Dashboard

| ID | Component | Severity | Description | Status | Verifying Test |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | `zara/static/index.html` | **High** | DOM-based XSS via direct `innerHTML` string injection | **RESOLVED** | Code Inspection & Sanitization |
| **SEC-02** | `zara/server.py` | **Medium** | Insecure CORS wildcard with `allow_credentials=True` | **RESOLVED** | `test_security_cors_policy` |
| **VOX-01** | `zara/voice_engine.py` | **High** | Corrupt WAV/PCM transcoding returning raw MP3 frames | **RESOLVED** | `test_tts_format_transcoding_wav_and_pcm` |
| **VOX-02** | `zara/voice_engine.py` | **Medium** | Loss of tone tags after paragraph 1 in multi-paragraph dialogue | **RESOLVED** | `test_silk_voice_prosody_parsing` |
| **VOX-03** | `zara/voice_engine.py` | **Medium** | Inline paralinguistics (`<sigh>`) stripped without acoustic pauses | **RESOLVED** | `test_silk_voice_prosody_parsing` |
| **MEM-01** | `zara/memory_engine.py` | **High** | Stopword token pollution and synonym blindness in memory retrieval | **RESOLVED** | `test_memory_stopword_and_category_boost` |
| **MEM-02** | `zara/memory_engine.py` | **Medium** | Case-sensitivity & syntax fragility in salient fact extractor | **RESOLVED** | `test_mesh_memory_engine` |
| **MEM-03** | `zara/memory_engine.py` | **Medium** | Blindness to compound relocation statements (historical city overriding current city) | **RESOLVED** | `test_compound_location_transition` |
| **MEM-04** | `zara/memory_engine.py` | **Medium** | Single-match truncation on multi-entity sentences (ignoring secondary pets/dislikes) | **RESOLVED** | `test_pet_relationship_extraction` |
| **CTX-01** | `zara/context_engine.py` | **Medium** | Missing client timezone offset causing false temporal greetings | **RESOLVED** | `test_context_sarcasm_and_timezone` |
| **CTX-02** | `zara/context_engine.py` | **Medium** | Sarcasm inversion misclassifying sarcastic distress as joy | **RESOLVED** | `test_context_sarcasm_and_timezone` |
| **SRV-01** | `zara/server.py` | **Medium** | WebSocket session crash on single malformed JSON payload frame | **RESOLVED** | `test_websocket_error_resilience` |
| **SRV-02** | `zara/server.py` | **Low** | Missing input length boundary clamping allowing oversized payload DoS | **RESOLVED** | `test_tts_input_length_limit` |
| **SRV-03** | `zara/server.py` | **Medium** | WebSocket rejection of parameterless control frames (`interrupt`/`stop` rejected with `EMPTY_TEXT`) | **RESOLVED** | `test_websocket_interruption_event` |
| **SRV-04** | `zara/server.py` | **Low** | Missing standard health probe and telemetry endpoints (`/v1/health` and `/v1/stats`) | **RESOLVED** | `test_health_and_stats_endpoints` |

---

## Detailed Defect Resolution Register

### 1. SEC-01: Stored/DOM-Based Cross-Site Scripting (XSS) in Frontend UI
* **Component**: `zara/static/index.html`
* **Severity**: **High**
* **Root Cause**: `appendMessage` and `refreshMemoryList` constructed DOM elements using direct string concatenation without HTML entity escaping.
* **Remediation**: Implemented strict HTML entity escaping (`escapeHtml()`) before applying emotion tags.
* **Status**: **RESOLVED & VERIFIED**

### 2. SEC-02: Insecure CORS Wildcard with Credentials
* **Component**: `zara/server.py`
* **Severity**: **Medium**
* **Root Cause**: FastAPI middleware configured with `allow_origins=["*"]` and `allow_credentials=True`.
* **Remediation**: Configured explicit origin whitelist (`http://localhost:8000`, etc.) and configurable `ZARA_ALLOWED_ORIGINS`.
* **Status**: **RESOLVED & VERIFIED**

### 3. VOX-01: Corrupt Audio Transcoding for WAV and PCM Formats
* **Component**: `zara/server.py` & `zara/voice_engine.py`
* **Severity**: **High**
* **Root Cause**: Synthesized MP3 bytes were returned with `media_type="audio/wav"` or `"audio/pcm"` without transcoding.
* **Remediation**: Integrated `pydub` to convert MP3 to genuine 24 kHz mono 16-bit RIFF WAV and signed 16-bit little-endian raw PCM.
* **Status**: **RESOLVED & VERIFIED**

### 4. VOX-02: Lack of Multi-Paragraph Tone Tag Parsing
* **Component**: `zara/voice_engine.py`
* **Severity**: **Medium**
* **Root Cause**: Tone tag parsing only evaluated the first paragraph of multi-paragraph dialogue.
* **Remediation**: Implemented `split_paragraphs_with_tones()` per Silk Muga 1 specification with 300ms inter-paragraph pause stitching.
* **Status**: **RESOLVED & VERIFIED**

### 5. VOX-03: Inline Vocalization Events Stripped Without Acoustic Effect
* **Component**: `zara/voice_engine.py`
* **Severity**: **Medium**
* **Root Cause**: Tags (`<sigh>`, `<chuckle>`) were stripped without acoustic pause or cadence adjustment.
* **Remediation**: Inserted natural acoustic ellipses breaks (`... `) and prosodic inflections for paralinguistic events.
* **Status**: **RESOLVED & VERIFIED**

### 6. MEM-01: Stopword Pollution and Synonym Blindness in Memory Retrieval
* **Component**: `zara/memory_engine.py`
* **Severity**: **High**
* **Root Cause**: Unweighted token intersection caused false-positive matches on stopwords and failed on synonyms.
* **Remediation**: Added 120+ English stopword dictionary and domain category keyword boosting (`CATEGORY_QUERY_KEYWORDS`).
* **Status**: **RESOLVED & VERIFIED**

### 7. MEM-02: Casing & Syntax Fragility in Fact Extractor
* **Component**: `zara/memory_engine.py`
* **Severity**: **Medium**
* **Root Cause**: Regex required title-case capital letters, ignoring lowercase disclosures.
* **Remediation**: Made regex patterns case-insensitive with automatic title-casing normalization.
* **Status**: **RESOLVED & VERIFIED**

### 8. MEM-03: Blindness to Compound Relocation Statements
* **Component**: `zara/memory_engine.py`
* **Severity**: **Medium**
* **Root Cause**: Compound statements like *"I used to live in Mumbai, but now I live in London"* matched the historical city instead of the current city.
* **Remediation**: Added compound relocation regex prioritizing the secondary current city capture and assigning `current_city` to the active location.
* **Status**: **RESOLVED & VERIFIED**
* **Verifying Test**: `tests/test_cognitive_and_realtime.py::test_compound_location_transition`

### 9. MEM-04: Single-Match Truncation on Multi-Entity Sentences
* **Component**: `zara/memory_engine.py`
* **Severity**: **Medium**
* **Root Cause**: Using `re.search` rather than `re.finditer` caused sentences with multiple pets or dislikes (*"My dog is Bruno and my cat is Luna"*) to only extract the first entity.
* **Remediation**: Refactored pet and dislike parsing to use `re.finditer`, capturing all entities in a single utterance.
* **Status**: **RESOLVED & VERIFIED**
* **Verifying Test**: `tests/test_cognitive_and_realtime.py::test_pet_relationship_extraction`

### 10. CTX-01: Lack of Client Timezone & Timestamp Handling
* **Component**: `zara/context_engine.py`
* **Severity**: **Medium**
* **Root Cause**: Clock used server system time, ignoring client timezone.
* **Remediation**: Added `client_tz_offset_minutes` support to calculate local hour from UTC datetime.
* **Status**: **RESOLVED & VERIFIED**

### 11. CTX-02: Sarcasm Inversion in Subtext Analysis
* **Component**: `zara/context_engine.py`
* **Severity**: **Medium**
* **Root Cause**: Positive adjectives (*"great"*) falsely tagged sarcastic complaints as joyful.
* **Remediation**: Implemented sarcasm pattern matching enthusiastic words followed by negative events (`sarcastic_frustration`).
* **Status**: **RESOLVED & VERIFIED**

### 12. SRV-01: WebSocket Crash on Malformed Frame
* **Component**: `zara/server.py`
* **Severity**: **Medium**
* **Root Cause**: Unhandled `JSONDecodeError` terminated WebSocket connections.
* **Remediation**: Added structured error emission (`MALFORMED_JSON`) while preserving the connection.
* **Status**: **RESOLVED & VERIFIED**

### 13. SRV-02: Missing Input Length Clamping
* **Component**: `zara/server.py`
* **Severity**: **Low**
* **Root Cause**: Payloads lacked character bounds.
* **Remediation**: Enforced `max_length=2000` clamping on TTS and chat requests.
* **Status**: **RESOLVED & VERIFIED**

### 14. SRV-03: WebSocket Rejection of Parameterless Control Frames
* **Component**: `zara/server.py`
* **Severity**: **Medium**
* **Root Cause**: WebSocket handler checked `if not text.strip(): return EMPTY_TEXT` before inspecting `action`, rejecting valid control frames like `{"action": "interrupt"}`.
* **Remediation**: Handled `action in ["interrupt", "stop"]` ahead of text validation, emitting `{"event": "interrupted", "status": "stream_halted"}`.
* **Status**: **RESOLVED & VERIFIED**
* **Verifying Test**: `tests/test_cognitive_and_realtime.py::test_websocket_interruption_event`

### 15. SRV-04: Missing Standard Health Probe and Telemetry Endpoints
* **Component**: `zara/server.py`
* **Severity**: **Low**
* **Root Cause**: Server lacked standard `/v1/health` and `/v1/stats` endpoints for Kubernetes probes and dashboard metrics.
* **Remediation**: Implemented `GET /v1/health` and `GET /v1/stats` returning service status, fact count, and turn volume.
* **Status**: **RESOLVED & VERIFIED**
* **Verifying Test**: `tests/test_cognitive_and_realtime.py::test_health_and_stats_endpoints`
