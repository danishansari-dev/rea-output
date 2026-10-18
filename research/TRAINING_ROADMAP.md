# Model Training & Fine-Tuning Roadmap
**Project Zara**: Long-Term Model Training, Compute Strategy & Governance  
**Document**: `research/TRAINING_ROADMAP.md`  
**Date**: October 18, 2026  
**Auditor**: Antigravity Clean-Room Reverse Engineering & AI Engineering Agent

---

## 1. Executive Strategy & Phased Progression

To prevent irresponsible compute expenditures while systematically building Zara's proprietary voice intelligence, Project Zara follows a **staged experimental progression**.

Each stage must satisfy explicit objective quality gates (MOS score, SIM score, WER) before capital or compute is committed to the subsequent stage:

```
┌────────────────────────────────────────────────────────┐
│             PHASE 1: SMALL PROOF-OF-CONCEPT            │
│ • 1x NVIDIA A10G (24GB) or Google Colab T4 (Free/Pro)  │
│ • 2 to 5 hours of clean, expressive voice recordings   │
│ • LoRA / QLoRA parameter-efficient fine-tuning         │
│ • Target: Validate tone tags ([whisper], [happy])      │
│ • Compute Cost: $0 (Colab Free) to $25 (Cloud GPU)     │
└───────────────────────────┬────────────────────────────┘
                            │ (Gate: SIM ≥ 0.80, WER ≤ 4.5%)
                            ▼
┌────────────────────────────────────────────────────────┐
│            PHASE 2: EMOTIONAL PERSONA ALIGNMENT        │
│ • 1x to 2x NVIDIA A100 (40GB/80GB) on RunPod / Lambda │
│ • 20 to 40 hours of multi-emotional paired audio       │
│ • Target: Full Zara voice identity lock-in             │
│ • Compute Cost: $150 – $350 (24–48 hours)              │
└───────────────────────────┬────────────────────────────┘
                            │ (Gate: MOS ≥ 4.2, SIM ≥ 0.86)
                            ▼
┌────────────────────────────────────────────────────────┐
│           PHASE 3: FOUNDATION MULTILINGUAL SCALE       │
│ • Multi-GPU Cluster (8x H100 / A100 SXM)               │
│ • 500+ hours of 22 Indic languages + Hinglish speech   │
│ • Target: Complete foundation speech language model    │
│ • Compute Cost: $8,000 – $20,000                       │
└────────────────────────────────────────────────────────┘
```

---

## 2. Phase 1: Small LoRA Pilot (Immediate Recommended Milestone)

### 2.1. Objectives
* Prove that parameter-efficient fine-tuning (LoRA, rank $r=8$ or $r=16$) on a small, high-quality audio corpus allows an open speech model (`rumik-ai/rumik-oss-1` or `Kokoro-82M` / `F5-TTS`) to adopt Zara's voice timbre and reliably trigger emotional inflections.
* Validate that `<laugh>` and `[whisper]` conditioning behaves naturally without phoneme distortion.

### 2.2. Dataset Scope
* **Volume**: 3 to 5 hours of single-speaker female voice recordings.
* **Content**: 60% English, 40% Hinglish banter, split into short utterances (3s to 12s).
* **Expressive Distribution**:
  - 150 neutral conversational clips.
  - 100 whispered intimate clips.
  - 100 joyful/playful clips with naturally punctuated laughter.
  - 50 empathetic/somber clips with sighs.

### 2.3. Compute & Cost
* **Environment**: Google Colab (with free T4 or Colab Pro A100) or 1x NVIDIA RTX 4090 / A10G instance on RunPod ($0.45 – $0.75/hr).
* **Training Duration**: ~6 to 10 hours.
* **Total Estimated Cost**: **$5 – $15 USD**.

---

## 3. Phase 2: Medium Voice Alignment

### 3.1. Objectives
* Fine-tune full acoustic attention layers to lock in Zara's unique persona across all conversational domains.
* Eliminate any trace of generic base assistant prosody.

### 3.2. Dataset Scope
* **Volume**: 25 to 40 hours of studio-recorded speech from an authorized voice actor.
* **Format**: 24-bit 48 kHz uncompressed WAV downsampled to 24 kHz mono, normalized to -23 LUFS.
* **Metadata**: Full forced-aligned phonetic transcripts, emotion labels, and pitch contours.

### 3.3. Compute & Cost
* **Environment**: 2x NVIDIA A100 (80GB) on Lambda Labs or RunPod ($3.80/hr total).
* **Training Duration**: 36 to 48 hours.
* **Total Estimated Cost**: **$150 – $250 USD**.

---

## 4. Phase 3: Foundation Multilingual Pre-Training

* Reserved for future commercial scaling when custom foundation weights are required.
* Involves pre-training an autoregressive transformer across 500–1,000 hours of multi-speaker Indic corpora (covering Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, etc.).
* Requires high-concurrency multi-node compute clusters (8x H100 nodes for 1–2 weeks).

---

## 5. Ethical Governance, Voice Actor Rights & Licensing

Project Zara operates under strict ethical standards:
1. **Zero Scraping Policy**: No copyrighted audio, celebrity voices, or unauthorized podcast rips will be used in model training.
2. **Biometric Consent Agreements**: Any professional voice actor contracted to record Zara's voice must sign an explicit biometric synthesis rider outlining:
   * Permitted domain (AI conversational companion).
   * Compensation (flat studio fee + optional usage royalties).
   * Prohibited domains (defamatory, fraudulent, political, or impersonation outputs).
3. **Open-Weights Compliance**:
   * Any experiments using `rumik-ai/rumik-oss-1` strictly observe its `CC-BY-NC-4.0` license (research, educational, and non-commercial exploration).
   * Commercial production deployments should build upon permissively licensed foundations (e.g. Kokoro under Apache 2.0 or F5-TTS under MIT).
