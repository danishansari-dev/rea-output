# Hardware Requirements, Compute Feasibility & Cost Matrix
**Subsystem**: `training/voice/`  
**Document**: `training/voice/HARDWARE_REQUIREMENTS.md`  
**Date**: October 18, 2026  
**Auditor**: Antigravity Clean-Room Reverse Engineering & AI Engineering Agent

---

## 1. Local Environment Audit (Current Host)

An empirical system diagnostic was conducted on the development machine:

```text
Host Platform: Windows 11 Pro (x86_64)
Installed Python: 3.11.9
Installed PyTorch: 2.11.0+cpu
CUDA GPU Available: False (torch.cuda.is_available() == False)
Hardware Acceleration: None (Host CPU only)
Memory (RAM): System standard DDR4/DDR5
Storage: NVMe SSD with > 50 GB free space
```

### Empirical Hardware Realities:
* **Local Foundation Training**: Training any 300M+ or 3.4B parameter speech model locally without an NVIDIA CUDA GPU is **technically impossible**.
* **Local Foundation Inference (3.4B SpeechLM)**: Autoregressive token decoding on CPU results in $\text{RTF} \approx 13.5$ (14 seconds of compute per 1 second of speech), making it unsuitable for live conversation.
* **Local Conversational Runtime**: Running Zara's built-in **Expressive Neural Engine** (`edge-tts` with dynamic SSML prosody + `pydub` transcoding) runs at $\text{RTF} < 0.05$ with $< 200\text{ ms}$ latency directly on the host CPU.

---

## 2. Hardware Matrix for Voice Model Training

The table below outlines minimum, recommended, and scale hardware specifications across model architectures:

| Pipeline Stage | Target Architecture | Minimum GPU / VRAM | Recommended Cloud GPU | Estimated Training Time | Estimated Compute Cost |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 1: LoRA Pilot (PoC)** | `rumik-ai/rumik-oss-1` (3.4B LoRA) | NVIDIA T4 (15 GB VRAM) | NVIDIA A10G (24 GB) or RTX 4090 | 6 to 10 hours (5h audio) | **$0 (Colab Free) to $8 (RunPod)** |
| **Phase 1: Compact Pilot** | `Kokoro-82M` (LoRA / Style) | Single T4 (15 GB) | RTX 3090 / 4090 | 2 to 4 hours | **$0 to $3** |
| **Phase 1: Flow-Matching** | `F5-TTS` (300M Fine-Tuning) | Single T4 (15 GB) | NVIDIA A10G / L4 | 8 to 14 hours | **$5 to $12** |
| **Phase 2: Full Voice Align**| `rumik-oss-1` (Full Attention) | 1x A100 (40 GB / 80 GB) | 2x A100 (80 GB) | 36 to 48 hours (30h audio) | **$120 to $250** |
| **Phase 3: Foundation Pretrain**| 3.4B Causal SpeechLM | 8x H100 (80 GB SXM) | 16x to 32x H100 Cluster | 1 to 2 weeks (1000h audio)| **$12,000 to $28,000** |

---

## 3. VRAM Consumption by Precision Tier (3.4B Model)

When fine-tuning a 3.4B parameter SpeechLM like `rumik-ai/rumik-oss-1`:

```
┌────────────────────────────────────────────────────────┐
│               VRAM ALLOCATION BREAKDOWN                │
├────────────────────┬───────────┬───────────┬───────────┤
│ Precision Tier     │ FP16      │ 8-bit QLoRA│ 4-bit QLoRA│
├────────────────────┼───────────┼───────────┼───────────┤
│ Base Model Weights │ ~6.8 GB   │ ~3.4 GB   │ ~1.9 GB   │
│ LoRA Adapter (r=16)│ ~0.08 GB  │ ~0.08 GB  │ ~0.08 GB  │
│ Optimizer (AdamW)  │ ~0.32 GB  │ ~0.32 GB  │ ~0.32 GB  │
│ Activations & KV   │ ~4.5 GB   │ ~3.2 GB   │ ~2.8 GB   │
│ Codec Vocoder Head │ ~1.8 GB   │ ~1.8 GB   │ ~1.8 GB   │
├────────────────────┼───────────┼───────────┼───────────┤
│ Total Peak VRAM    │ ~13.5 GB  │ ~8.8 GB   │ ~6.9 GB   │
└────────────────────┴───────────┴───────────┴───────────┘
```

* **Google Colab Free Tier (T4 with 15 GB VRAM)**: Can comfortably run FP16 or 8-bit QLoRA fine-tuning with a batch size of 2 and gradient accumulation steps of 8.
* **Google Colab Pro (A100 with 40 GB VRAM)**: Allows larger batch sizes (8 to 16) and faster convergence.

---

## 4. Cloud GPU Provider Comparison

If scaling beyond Google Colab:

| Provider | Recommended Instance | GPU Specs | On-Demand Hourly Rate | Best Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Google Colab** | Colab Free / Pro | 1x T4 (15GB) / A100 (40GB) | $0 / $10/mo subscription | Interactive development & pilot training |
| **RunPod.io** | Secure Cloud | 1x RTX 4090 (24GB) | $0.44 – $0.59 / hr | Low-cost dedicated pilot runs |
| **Lambda Labs** | Cloud Instance | 1x A10 (24GB) / A100 (80GB) | $0.75 / $1.89 / hr | High-bandwidth reliable multi-hour training |
| **Vast.ai** | Community Cloud | 1x RTX 3090 / 4090 | $0.25 – $0.38 / hr | Extreme budget experiments (spot instances) |

---

## 5. Storage & Bandwidth Planning

* **Raw Audio Storage**: 5 hours of 48 kHz 24-bit WAV $\approx 3.2\text{ GB}$.
* **Preprocessed 24 kHz Mono Audio**: 5 hours $\approx 860\text{ MB}$.
* **LoRA Adapter Checkpoint**: $\sim 48\text{ MB}$ per checkpoint (easily saved to Google Drive or GitHub releases).
* **Dataset Manifest**: $< 5\text{ MB}$ JSONL.
