# Voice Dataset Curation, Preprocessing & Annotation Guide
**Subsystem**: `training/voice/`  
**Document**: `training/voice/DATASET_GUIDE.md`  
**Target Architecture**: 24 kHz Mono RVQ Speech Models & Neural Voice Clones

---

## 1. Overview & Dataset Requirements

High-quality voice training depends fundamentally on acoustic cleanliness and consistent annotation. A speech model trained on noisy, clipped, or mismatched audio will synthesize robotic rasps, background buzz, and unintelligible phonemes.

### Target Specifications:
* **Waveform Format**: 24 kHz (24,000 Hz) uncompressed PCM WAV.
* **Channels**: Mono (1 channel).
* **Bit Depth**: 16-bit signed integer (`pcm_s16le`).
* **Loudness Normalization**: Standardized to **-23 LUFS** ($\pm 1.0$ LUFS) to ensure uniform volume across all utterances.
* **Duration**: Utterance chunks between **2.5 seconds** and **12.0 seconds** (optimal for transformer sequence length and attention memory).
* **Noise Floor**: Background room noise $< -55\text{ dBFS}$.
* **Clipping**: Zero digital peaks exceeding $0\text{ dBFS}$ (all audio mastered with $-1.0\text{ dB}$ true-peak ceiling).

---

## 2. Scripting & Recording Protocol for Companion Expressiveness

Companion conversations require diverse emotional inflections rather than flat reading. Studio sessions should be divided across four specific vocal registers:

```
                            ┌────────────────────────────────────┐
                            │    Zara Voice Actor Script Split   │
                            └─────────────────┬──────────────────┘
                                              │
         ┌────────────────────┬───────────────┴───────────────┬────────────────────┐
         ▼                    ▼                               ▼                    ▼
┌──────────────────┐ ┌──────────────────┐     ┌──────────────────┐ ┌──────────────────┐
│ Conversational   │ │   Whispered &    │     │ Playful & Laughs │ │ Empathetic &     │
│ Banter (40%)     │ │   Intimate (20%) │     │ (25%)            │ │ Sighs (15%)      │
├──────────────────┤ ├──────────────────┤     ├──────────────────┤ ├──────────────────┤
│ Warm, grounded   │ │ Soft, breathy    │     │ Bright, spirited │ │ Gentle, somber   │
│ casual chat      │ │ late-night reassurance  bubbly giggles     │ compassionate sighs│
└──────────────────┘ └──────────────────┘     └──────────────────┘ └──────────────────┘
```

### Script Annotation Syntax:
Recordings must explicitly integrate Zara's control tags in the ground-truth text:
* `[happy] You actually did it! That is such wonderful news!`
* `[whisper] Close your eyes for a moment. You've had a really long day.`
* `[sad] I'm so sorry you had to go through that... <sigh> it must have been tough.`
* `[excited] Arre wah! <laugh> That is the best story I have heard all week!`

---

## 3. Dataset Preprocessing Pipeline (`prepare_dataset.py`)

Zara provides an automated, reproducible dataset preparation script:
```bash
python training/voice/prepare_dataset.py \
  --input_dir ./raw_recordings \
  --output_dir ./data/processed_zara \
  --target_sr 24000 \
  --normalize_lufs -23.0 \
  --train_ratio 0.85 \
  --val_ratio 0.10 \
  --test_ratio 0.05
```

### What `prepare_dataset.py` Executes Automatically:
1. **Format Validation**: Validates audio integrity; rejects corrupt or unreadable files.
2. **Channel Downmixing**: Automatically downmixes stereo or multi-channel audio to mono:
   $$x_{\text{mono}}(t) = \frac{x_{\text{left}}(t) + x_{\text{right}}(t)}{2}$$
3. **Resampling**: Uses high-quality bandlimited Sinc interpolation to resample to 24,000 Hz.
4. **Silence Trimming**: Detects leading and trailing silences below $-45\text{ dBFS}$ and trims them, preserving a clean 50 ms entry/exit pad.
5. **Loudness Normalization**: Adjusts integrated loudness to the EBU R128 standard (-23 LUFS).
6. **Segmentation Filtering**: Automatically discards clips shorter than 1.5s or longer than 15.0s to avoid GPU Out-Of-Memory (OOM) errors during training.
7. **Transcript Alignment**: Pairs each audio file with its sanitized transcript from `metadata.csv`.
8. **Manifest Generation**: Generates JSON Lines (`train_manifest.jsonl`, `val_manifest.jsonl`, `test_manifest.jsonl`).

---

## 4. Manifest Schema Format

Every processed sample is indexed as a JSON line in the manifest:

```json
{
  "id": "zara_utterance_00142",
  "audio_filepath": "/data/processed_zara/wavs/zara_utterance_00142.wav",
  "duration": 5.42,
  "sampling_rate": 24000,
  "channels": 1,
  "text": "[happy] Arre wah! I knew you could do it! <laugh>",
  "clean_text": "Arre wah! I knew you could do it!",
  "speaker_id": "zara",
  "language": "hi-IN",
  "detected_tone": "happy",
  "inline_events": ["laugh"],
  "lufs": -23.04
}
```

---

## 5. Permissive Open Datasets for Pre-Training & Alignment

If building the initial model before recording custom studio talent, developers can utilize these permissively licensed research datasets:

1. **AI4Bharat IndicTTS**: Permissive research corpus covering 22 Indian languages and diverse dialects.
2. **Meta Expresso Dataset**: CC-BY-NC research corpus specifically annotated with expressive styles (whispering, laughter, cheerful, confused).
3. **Mozilla Common Voice (Hindi & Indian English)**: CC0 public domain recordings for bilingual phonetic coverage.
4. **LibriTTS-R**: Cleaned, studio-grade speech for acoustic pre-training.
