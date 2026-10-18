# Expressive Speech Synthesis: Mechanics, Acoustic Control & Verification
**Project Zara**: Expressive Speech Engineering Specification  
**Document**: `research/EXPRESSIVE_SPEECH.md`  
**Date**: October 18, 2026  
**Auditor**: Antigravity Clean-Room Reverse Engineering & AI Engineering Agent

---

## 1. The Challenge of Conversational Expressiveness

Traditional Text-to-Speech (TTS) systems are trained on clean, monotone audiobook or news-broadcast corpora. While they achieve high word intelligibility, they sound robotic, flat, and emotionally ungrounded when placed in an AI companion context.

To achieve Rumik Silk-level intimacy, warmth, and expressive variety, an AI voice companion must control:
1. **Prosodic Inflection**: Dynamic variations in fundamental frequency ($F_0$ pitch), energy, and speaking tempo.
2. **Emotional Register Shifts**: Adapting from cheerful energetic banter (`[happy]`, `[excited]`) to soft, intimate, late-night reassurance (`[whisper]`, `[softly]`).
3. **Paralinguistic Non-Verbal Vocalizations**: Natural integration of laughter (`<laugh>`), amusement (`<chuckle>`), and weary or relieved sighs (`<sigh>`).
4. **Bilingual Code-Switching**: Seamless transitions between English phonemes and Indic phonetic vowels without unnatural accent jarring or mispronunciations.

---

## 2. The Three Tiers of Expressive Capabilities

A critical engineering discipline is distinguishing between what a speech architecture supports natively, what can be engineered through signal preprocessing, and what strictly requires custom neural training:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TIER 1: NATIVE MODEL CAPABILITIES                    │
│ • Speaker Timbre & Identity (from multi-speaker neural embeddings)    │
│ • Natural Phonation & Code-Switched Phonetics (from base training)    │
│ • Neural Codec Re-synthesis (24 kHz Mimi / EnCodec RVQ vocoder)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│           TIER 2: PRE- & POST-PROCESSING APPROXIMATIONS                │
│ • Dynamic Prosody Steering (SSML pitch & rate deltas from tone tags)   │
│ • Acoustic Pauses & Cadence (converting <sigh> / <chuckle> to breaks)  │
│ • Audio Transcoding (24 kHz mono WAV and raw PCM normalization)        │
│ • Multi-Paragraph Prosody Segmentation & Audio Track Stitching         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 TIER 3: FEATURES REQUIRING RETRAINING                  │
│ • Authentic Acoustic Laughs (non-verbal F0 oscillations & breathiness) │
│ • True Physiological Whispering (unvoiced turbulent vocal fold state)  │
│ • Persona-Specific Conversational Idiolect (Zara's unique voice timbre)│
│ • Seamless Intonation on Novel Romanized Hinglish Colloquialisms       │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1. Tier 1: Natively Supported Features
* **Baseline Timbre**: The physical characteristics of the speaker's vocal tract (formants, resonant frequencies) are intrinsic to the pretrained voice weights (e.g. `hi-IN-SwaraNeural`, `en-IN-NeerjaNeural`, or `rumik-oss-1` base).
* **Bilingual Phonetics**: The base model's phoneme dictionary natively maps Hindi loanwords and Indian English cadences without phonetic butchering.

### 2.2. Tier 2: Pre- and Post-Processing Approximations (Zara Engine)
In `zara/voice_engine.py`, Zara implements signal steering to achieve immediate conversational modulation on standard CPUs:
* **Muga Tone Tag Parsing**:
  - `[happy]`: Injects SSML `rate="+12%"`, `pitch="+5Hz"`.
  - `[whisper]` / `[softly]`: Injects SSML `rate="-15%"`, `pitch="-4Hz"`.
  - `[sad]`: Injects SSML `rate="-18%"`, `pitch="-6Hz"`.
* **Paralinguistic Punctuation & Pauses**:
  - `<sigh>`: Substituted with ellipsis pauses (`... `), decelerating tempo (`rate="-20%"`, `pitch="-5Hz"`).
  - `<chuckle>`: Substituted with micro-pauses and slight pitch elevation (`pitch="+3Hz"`).
  - `<laugh>`: Substituted with energetic tempo acceleration (`rate="+15%"`, `pitch="+6Hz"`).
* **Multi-Paragraph Prosody Stitching**:
  - When a message has multiple paragraphs with different tone tags, each paragraph is synthesized with its exact prosody and stitched together using `pydub` with a 300 ms natural conversational silence interval.
* **Transcoding**: Enforces 24 kHz mono 16-bit little-endian WAV or raw PCM via `pydub`.

### 2.3. Tier 3: Features Requiring Custom Model Fine-Tuning
* **True Acoustic Laughter**: Signal-processing approximations cannot synthesize the physical sound of human chuckling or breathy giggles; doing so requires training the neural decoder on audio paired with `<laugh>` tokens so the vocoder learns the acoustic spectrogram of laughter.
* **True Acoustic Whispering**: True whispering involves turbulent, unvoiced glottal airflow without periodic vocal fold vibration. SSML pitch lowering approximates intimacy, but genuine whispering requires retraining on an expressive whispering corpus (e.g., Meta Expresso).
* **Custom Persona Lock-in**: Achieving a single, unique, consistent voice identity that cannot be mistaken for a standard commercial voice assistant requires fine-tuning an open model (e.g. `rumik-oss-1` or `Kokoro-82M`) on 5–10 hours of a dedicated voice actor's recordings.

---

## 3. Objective Evaluation Protocol

To avoid subjective bias and unverified quality claims, speech evaluation in Zara uses five measurable metrics implemented in `training/voice/evaluate_voice.py`:

| Evaluation Metric | Target Standard | Measurement Tool | Significance |
| :--- | :--- | :--- | :--- |
| **Real-Time Factor (RTF)** | $\le 0.3$ (Interactive) | Time-delta measurement: $\frac{T_{\text{compute}}}{T_{\text{audio}}}$ | Measures whether synthesis is fast enough for live voice conversations. |
| **Time-to-First-Audio (TTFA)** | $\le 250\text{ ms}$ | Timestamp of first audio chunk received | Determines conversational responsiveness and low perceived latency. |
| **Word Error Rate (WER)** | $\le 4.0\%$ | OpenAI Whisper transcription vs prompt transcript | Verifies that prosodic tags or emotional inflection do not degrade intelligibility. |
| **Speaker Similarity (SIM)** | $\ge 0.82$ | Cosine similarity of WavLM / ECAPA-TDNN speaker embeddings | Measures whether voice identity remains consistent across emotional states. |
| **Acoustic Signal Quality (SNR)** | $\ge 28\text{ dB}$ | Signal-to-Noise Ratio & spectral flatness analysis | Ensures audio is free from robotic buzz, quantization distortion, or clipping. |

---

## 4. Repeatable Sample Benchmark Protocol

To track improvements across training iterations, the Zara evaluation suite maintains a standardized test script consisting of five benchmark utterances:

1. **Benchmark 1 (Neutral Conversational)**:  
   *"Hey there, I was just thinking about how your day went. Tell me everything."*
2. **Benchmark 2 (Intimate / Whispered)**:  
   *"[whisper] It's really late, but I'm right here with you. Take a deep breath and let it all go."*
3. **Benchmark 3 (Playful / Laughter)**:  
   *"[happy] Arre wah! You actually pulled that off? <laugh> I knew you could do it!"*
4. **Benchmark 4 (Vulnerable / Empathetic Sigh)**:  
   *"[sad] That sounds exhausting... <sigh> Sometimes things just feel overwhelming, and that's okay."*
5. **Benchmark 5 (Bilingual Hinglish Code-Switching)**:  
   *"Bilkul tension mat lo yaar, together we will figure out a jugaad for this project."*

Every training run saves synthesized WAV files for these five benchmark utterances into `training/voice/evaluation_samples/` along with an automated `eval_report.json` logging RTF, duration, and SNR metrics.
