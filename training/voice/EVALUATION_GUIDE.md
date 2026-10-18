# Speech Model Evaluation, Acoustic Benchmarks & Quality Protocol
**Subsystem**: `training/voice/`  
**Document**: `training/voice/EVALUATION_GUIDE.md`  
**Target Quality Standards**: Objective Acoustic Metrics & Human Listening Protocols

---

## 1. Overview & Evaluation Philosophy

A speech model cannot be evaluated purely by loss curves. A model with low cross-entropy loss may still produce unnatural prosody, metallic artifacts, or phonetic slurring.

Zara establishes a **dual-tier evaluation protocol**:
1. **Automated Objective Metrics**: Programmatic, repeatable measurements of latency, intelligibility, speaker similarity, and signal quality.
2. **Subjective Human Protocol**: Double-blind Mean Opinion Score (MOS) evaluations assessing conversational warmth, naturalness, and empathy.

---

## 2. Objective Metric Definitions & Benchmarks

```
┌────────────────────────────────────────────────────────────────────────┐
│                      OBJECTIVE SPEECH BENCHMARKS                       │
├──────────────────────┬────────────────────────┬────────────────────────┤
│ Metric               │ Target Specification   │ Measurement Method     │
├──────────────────────┼────────────────────────┼────────────────────────┤
│ Real-Time Factor     │ RTF ≤ 0.30 (Real-time) │ T_compute / T_audio    │
│ Time-to-First-Audio  │ TTFA ≤ 250 ms          │ First chunk timestamp  │
│ Word Error Rate      │ WER ≤ 4.0%             │ Whisper Large v3 ASR   │
│ Speaker Similarity   │ SIM ≥ 0.82             │ WavLM Cosine Sim       │
│ Signal-to-Noise      │ SNR ≥ 28 dB            │ Spectral SNR           │
│ Tag Adherence        │ 100% (No tag leakage)  │ Regex transcript match │
└──────────────────────┴────────────────────────┴────────────────────────┘
```

### 2.1. Real-Time Factor (RTF)
Measures computational efficiency:
$$\text{RTF} = \frac{\text{Wall-clock Synthesis Time (seconds)}}{\text{Duration of Synthesized Audio (seconds)}}$$
* $\text{RTF} < 1.0$: Model synthesizes faster than real time.
* $\text{RTF} \le 0.30$: **Interactive conversational threshold**. Audio starts streaming before the user notices delay.

### 2.2. Word Error Rate (WER) via ASR
Measures speech intelligibility by transcribing the synthesized audio using OpenAI Whisper:
$$\text{WER} = \frac{S + D + I}{N}$$
Where:
* $S$ = Substitutions, $D$ = Deletions, $I$ = Insertions, $N$ = Total reference words.
* Target: $\text{WER} \le 4.0\%$ on standard conversational English and Hinglish phrases.

### 2.3. Speaker Similarity (SIM Score)
Measures voice identity consistency across emotional shifts:
1. Extract 512-dimensional speaker embedding vector $\mathbf{v}_{\text{ref}}$ from 5 reference audio clips of the voice actor using `microsoft/wavlm-base-plus-sv`.
2. Extract speaker embedding $\mathbf{v}_{\text{synth}}$ from the synthesized checkpoint clip.
3. Compute cosine similarity:
   $$\text{SIM}(\mathbf{v}_{\text{ref}}, \mathbf{v}_{\text{synth}}) = \frac{\mathbf{v}_{\text{ref}} \cdot \mathbf{v}_{\text{synth}}}{\|\mathbf{v}_{\text{ref}}\| \|\mathbf{v}_{\text{synth}}\|}$$
* Target: $\text{SIM} \ge 0.82$.

### 2.4. Signal Quality (SNR & Clipping)
* Signal-to-Noise Ratio (SNR) calculated over active speech frames vs background silence. Target: $\ge 28\text{ dB}$.
* Zero digital clipping (max absolute sample $< 0.99$).

---

## 3. Automated Benchmark Execution (`evaluate_voice.py`)

Zara provides an automated evaluation script that synthesizes the 5 standardized benchmark phrases, measures objective metrics, and saves the output:

```bash
python training/voice/evaluate_voice.py \
  --output_dir ./evaluation_results \
  --voice_name zara-expressive
```

### Generated Outputs:
1. `evaluation_results/eval_report.json`: Full structured JSON logging:
   * Per-sample synthesis latency, duration, and RTF.
   * Signal-to-Noise Ratio (SNR).
   * Tone tag verification (confirms tags like `[happy]` or `<laugh>` are processed and not spoken aloud).
2. `evaluation_results/wavs/`: Five 24 kHz WAV audio files representing each benchmark scenario.

---

## 4. Subjective Mean Opinion Score (MOS) Protocol

For milestone releases, conduct double-blind MOS evaluations with 10–20 bilingual human listeners:
* **Scale (1 to 5)**:
  * 5: Completely natural, warm, indistinguishable from a human companion.
  * 4: Natural and pleasant with slight synthetic inflection.
  * 3: Understandable but noticeable robotic pacing or prosodic flatness.
  * 2: Stiff, jarring pitch shifts, or distracting acoustic buzz.
  * 1: Unintelligible or completely unnatural.
* **Evaluation Dimensions**:
  1. *Naturalness*: Does the speech flow like real conversation?
  2. *Emotional Resemblance*: Does `[whisper]` convey true intimacy? Does `[happy]` convey genuine joy?
  3. *Hinglish Fluency*: Are Hindi loanwords pronounced organically?
