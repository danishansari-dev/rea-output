# Zara Voice Training & Fine-Tuning Pipeline
**Subsystem**: `training/voice/`  
**Purpose**: Complete, reproducible pipeline for training, fine-tuning, evaluating, and exporting custom voice models for Zara.  
**Hardware Compatibility**: Google Colab (T4 / A100), Cloud GPU (RunPod / Lambda A10G / RTX 4090), and Local CPU (Dataset Preparation & Evaluation).

---

## 1. Directory Structure & Components

```text
training/voice/
├── README.md                      # Pipeline overview and quickstart (this file)
├── DATASET_GUIDE.md               # Audio curation, normalization, and tagging guide
├── MODEL_SELECTION.md             # In-depth model evaluation and architecture selection
├── TRAINING_GUIDE.md              # Step-by-step training, LoRA, and hyperparameter guide
├── EVALUATION_GUIDE.md            # Objective acoustic metrics (WER, RTF, SIM, SNR) guide
├── HARDWARE_REQUIREMENTS.md       # VRAM, compute time, and cost matrix
├── prepare_dataset.py             # Executable audio preprocessing & manifest generator
├── train_voice.py                 # Executable PyTorch fine-tuning engine with LoRA & checkpointing
├── evaluate_voice.py              # Executable voice quality evaluation and benchmark script
├── zara_voice_training.ipynb      # Complete, restartable Google Colab Jupyter Notebook
├── configs/                       # Hyperparameter configuration JSONs
│   └── lora_pilot_config.json
└── evaluation_samples/            # Directory where synthesized benchmark WAVs are persisted
```

---

## 2. Quickstart: 3-Step Training Workflow

### Step 1: Prepare Your Voice Dataset
Place raw audio recordings (`.wav` or `.mp3`) and a `metadata.csv` (or `.jsonl`) into a dataset directory:
```bash
python training/voice/prepare_dataset.py --input_dir ./raw_audio --output_dir ./processed_dataset --target_sr 24000 --normalize_lufs -23
```
This automatically validates file formats, resamples to 24 kHz mono, normalizes loudness to -23 LUFS, trims silence, validates transcripts, and generates `train_manifest.jsonl` and `val_manifest.jsonl`.

### Step 2: Run Fine-Tuning (Google Colab or Cloud GPU)
Launch the restartable notebook:
`training/voice/zara_voice_training.ipynb`
Or run directly via command line on a GPU machine:
```bash
python training/voice/train_voice.py --config training/voice/configs/lora_pilot_config.json --manifest ./processed_dataset/train_manifest.jsonl --output_dir ./checkpoints/zara_pilot_v1
```

### Step 3: Evaluate Checkpoint & Generate Benchmarks
Measure objective audio quality, Real-Time Factor (RTF), and emotion tag adherence:
```bash
python training/voice/evaluate_voice.py --checkpoint ./checkpoints/zara_pilot_v1 --output_dir ./evaluation_results
```

---

## 3. Supported Model Lineages

| Architecture | Parameters | Target Hardware | License | Strengths |
| :--- | :--- | :--- | :--- | :--- |
| **Rumik OSS 1 (Llama-Mimi)** | 3.4 Billion | GPU ($\ge 16\text{ GB}$ VRAM) | CC-BY-NC-4.0 | Native Mimi 24kHz RVQ tokens, 22 Indic scripts, code-switching |
| **Kokoro-82M** | 82 Million | CPU or Small GPU | Apache 2.0 | Ultra-fast ($\text{RTF} < 0.25$ on CPU), compact, permissive |
| **F5-TTS (Flow-Matching)** | 300 Million | GPU ($\ge 8\text{ GB}$ VRAM) | MIT | Stable non-autoregressive cloning, rapid training convergence |
| **Zara Expressive Neural** | Cloud Neural | Any Device / CPU | Permissive API | Instant $< 200\text{ ms}$ streaming, dynamic SSML prosody |
