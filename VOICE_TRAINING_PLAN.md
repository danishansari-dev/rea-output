# Technical Plan: Training & Fine-Tuning an Expressive Conversational Voice Model

## 1. Executive Summary & Objective

The objective of this technical plan is to train or fine-tune an open-weights, high-fidelity neural voice model capable of matching Rumik Silk's expressive traits:
* Consistent speaker persona and timbre.
* Dynamic emotional inflection (joy, sorrow, calm, excitement, intimacy).
* Natural prosodic pauses, pacing, and rhythm.
* Realistic non-verbal vocalizations: whispering, laughing (`<laugh>`), sighing (`<sigh>`), chuckling (`<chuckle>`).
* Seamless code-switching between English and Indic languages (Hinglish).

To protect against irresponsible compute expenditure, this plan outlines a **phased progression**: starting with a small, low-cost proof-of-concept (LoRA / prompt-tuning / flow-matching adaptation) before considering full-scale foundation training.

---

## 2. Dataset Strategy & Ethical Governance

### 2.1. Consent, Licensing & Voice Actor Rights
* **Zero Scraping Policy**: No copyrighted audio, scraped podcasts, or celebrity voices without explicit written commercial licenses and biometric consent.
* **Actor Consent Agreement**: Voice talent must sign explicit digital voice synthesis riders detailing:
  - Scope of use (AI conversational companion).
  - Compensation structure (per-hour recording fee + optional token royalty).
  - Explicit right of revocation or restriction on defamatory/harmful outputs.
* **Permissive Open Datasets for Pre-Training / Alignment**:
  - *IndicTTS / AI4Bharat*: Permissive research corpora covering 22 Indian languages.
  - *Common Voice (Mozilla)*: CC0 / CC-BY multilingual speech recordings.
  - *Expresso Dataset (Meta)*: Public benchmark specifically containing labeled expressive styles (whispering, laughter, singing, confused, cheerful).

### 2.2. Script Design & Recording Protocol
To capture the specific conversational traits needed for an AI companion:
1. **Interactive Banter Scripts**: Recording real dialog turns rather than formal audiobook reading.
2. **Explicit Paralinguistic Tokens**:
   - 200+ samples of laughter integrated naturally into sentences.
   - 100+ samples of sighs, chuckles, and gasps.
   - 150+ samples of intimate whispering (reduced vocal fold vibration, high breathiness).
3. **Studio Environment**:
   - 24-bit 48 kHz uncompressed WAV.
   - Anechoic chamber or treated vocal booth with $< -60\text{ dB}$ noise floor.
   - Large diaphragm condenser microphone (e.g. Neumann U87 or Shure SM7B).

### 2.3. Audio Preprocessing Pipeline
```
  [ Raw 48kHz WAV ] ──► [ Silence Trimming ] ──► [ LUFS Normalization (-23 LUFS) ]
                            │
                            ▼
             [ Kyutai Mimi Codec Encoder (24kHz) ]
                            │
                            ▼
     [ 8-Layer Residual Vector Quantized Tokens (RVQ) ]
```
1. Resample to 24 kHz mono.
2. Align audio with phonetic transcripts using WhisperX / CTC Forced Alignment.
3. Quantize continuous waveforms into discrete acoustic tokens using Kyutai Mimi or EnCodec (8 codebooks, 24 kHz).

---

## 3. Model Architecture Options

We evaluate two distinct paths for expressive model construction:

### Architecture Option A: Causal Autoregressive Speech LM (Rumik OSS 1 Style)
* **Backbone**: Pre-trained causal language model (e.g., `CohereLabs/tiny-aya-fire` 3.4B or `Llama-3.2-1B-Instruct`).
* **Audio Representation**: Kyutai Mimi neural audio codec (8 codebooks, 24 kHz, ~12.5 Hz frame rate).
* **Interleaved Token Stream**:
  $$\mathbf{X} = [\text{Text Tokens}, \langle\text{audio}\rangle, c_{1,1}, \dots, c_{8,1}, c_{1,2}, \dots, c_{8,2}, \langle/\text{audio}\rangle]$$
* **Steering Mechanism**: Special tokens inserted in text prefix (`[happy]`, `[whisper]`) or description embeddings.
* **Pros**: Native integration of laughter and sighs as tokens; unified text and speech representations.
* **Cons**: High inference latency; requires dedicated CUDA GPU (VRAM $\ge 12\text{ GB}$).

### Architecture Option B: Flow-Matching Zero-Shot Voice Model (F5-TTS Style)
* **Backbone**: Diffusion Transformer (DiT) with Flow Matching.
* **Audio Representation**: Continuous Mel-spectrogram + HiFi-GAN / BigVGAN vocoder.
* **Conditioning**: 3 to 10 second audio reference clip providing voice identity and emotional tone.
* **Pros**: Faster convergence (10–50 hours training); extremely stable voice cloning; non-autoregressive parallel generation.
* **Cons**: Harder to steer via explicit inline tags without extensive paired expressive data.

---

## 4. Phased Experimentation & Feasibility Analysis

```
┌─────────────────────────────────┐
│ Phase 1: Small LoRA Pilot (PoC) │ ◄── Current Recommended Entry Point
│ - 5 hours of licensed speech    │
│ - 1x RTX 4090 (24GB) or A10G    │
│ - Cost: ~$25 - $50 (Cloud GPU)  │
│ - Target: Test tone tags        │
└────────────────┬────────────────┘
                 │ (If MOS > 3.8 and tags work)
                 ▼
┌─────────────────────────────────┐
│ Phase 2: Medium Voice Alignment │
│ - 30 hours of expressive speech │
│ - 4x A100 (80GB) for 48 hours   │
│ - Cost: ~$400 - $600            │
│ - Target: Full speaker persona  │
└────────────────┬────────────────┘
                 │ (If commercial deployment justified)
                 ▼
┌─────────────────────────────────┐
│ Phase 3: Foundation Model Train │
│ - 1,000+ hours multi-speaker    │
│ - 8x H100 cluster for 2 weeks   │
│ - Cost: ~$12,000 - $25,000      │
└─────────────────────────────────┘
```

### 4.1. Proposed Phase 1: The Small Pilot Experiment
* **Objective**: Validate whether fine-tuning `rumik-ai/rumik-oss-1` or `Kokoro` with LoRA on 5 hours of an actor's voice accurately locks in Zara's unique identity and responds to `[whisper]` and `<laugh>`.
* **Dataset**: 5 hours of curated Hinglish and English recordings by a single female voice actor.
* **Hardware**: 1x NVIDIA A10G (24 GB VRAM) on RunPod / Lambda Labs ($0.75/hr).
* **Expected Training Time**: 12–16 hours.
* **Total Estimated Cost**: **$15 – $30 USD**.
* **Risk**: Extremely low; gives immediate empirical feedback on data quality and voice stability before capital commitment.

---

## 5. Evaluation Protocol

A trained checkpoint must pass rigorous automated and subjective benchmarks before deployment:
1. **Speaker Verification (SIM Score)**:
   - Calculate cosine similarity of speaker embeddings (WavLM / ECAPA-TDNN) between synthesized audio and ground-truth actor clips. Target: $\ge 0.82$.
2. **Word Error Rate (WER)**:
   - Transcribe synthesized speech with OpenAI Whisper Large v3. Target: $\text{WER} \le 3.5\%$.
3. **Paralinguistic Event Accuracy**:
   - Verify that `<laugh>` generates audible acoustic bursts ($F_0$ oscillation, breathiness) rather than speaking the word "laugh".
4. **Subjective Mean Opinion Score (MOS)**:
   - Double-blind evaluation with 20 bilingual (English + Hindi) human raters assessing naturalness, warmth, and emotion on a 1–5 scale. Target: $\text{MOS} \ge 4.2$.
