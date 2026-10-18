# Voice Model Training, LoRA Fine-Tuning & Checkpoint Guide
**Subsystem**: `training/voice/`  
**Document**: `training/voice/TRAINING_GUIDE.md`  
**Target Architecture**: Causal Speech Language Models & Parameter-Efficient LoRA

---

## 1. Mathematical Formulation & Training Objective

Training a causal Speech Language Model (SpeechLM) with interleaved text and acoustic tokens involves optimizing the autoregressive cross-entropy loss over a discrete sequence:

$$\mathcal{L}(\theta) = -\sum_{t=1}^{T} \log P_\theta(s_t \mid s_{<t})$$

Where $s_t$ can be either:
1. A text token $w \in \mathcal{V}_{\text{text}}$ (multilingual vocabulary).
2. A discrete acoustic token $c_j \in \mathcal{V}_{\text{codec}}$ belonging to RVQ codebook level $j \in \{1, \dots, 8\}$.
3. A special emotional control token ($[\text{happy}]$, $[\text{whisper}]$, $\langle\text{laugh}\rangle$, $\langle\text{sigh}\rangle$).

---

## 2. Parameter-Efficient Fine-Tuning with LoRA

Because foundation SpeechLMs contain ~3.4B parameters, full-parameter fine-tuning requires 4x to 8x A100 GPUs ($> 300\text{ GB}$ aggregated VRAM). 

Zara's training pipeline implements **Low-Rank Adaptation (LoRA)**, freezing the base transformer weights $W_0 \in \mathbb{R}^{d \times k}$ and injecting trainable rank decomposition matrices:

$$W = W_0 + \Delta W = W_0 + \frac{\alpha}{r} (B \cdot A)$$

Where:
* $A \in \mathbb{R}^{r \times k}$ is initialized from a Gaussian distribution $\mathcal{N}(0, \sigma^2)$.
* $B \in \mathbb{R}^{d \times r}$ is initialized to zero, ensuring $\Delta W = 0$ at the start of training.
* $r \ll \min(d, k)$ is the low-rank dimension (typically $r = 8$ or $r = 16$).
* $\alpha$ is a scaling factor (typically $\alpha = 2 \times r = 32$).

### Advantages for Zara:
* **Trainable Parameters**: Reduces trainable weights from 3.4 billion down to **~12 to 24 million parameters** ($< 0.5\%$ of the model).
* **VRAM Footprint**: Enables fine-tuning in FP16 / BF16 on a single **NVIDIA T4 (15 GB)** or **A10G (24 GB)** GPU.
* **Storage**: Checkpoints require only **~50 MB** per checkpoint instead of 7 GB, enabling rapid versioning and persistence to Google Drive.

---

## 3. Recommended Hyperparameters for the Pilot Experiment

```json
{
  "model_name_or_path": "rumik-ai/rumik-oss-1",
  "lora_r": 16,
  "lora_alpha": 32,
  "lora_dropout": 0.05,
  "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
  "learning_rate": 2e-4,
  "min_learning_rate": 1e-5,
  "lr_scheduler_type": "cosine",
  "warmup_ratio": 0.06,
  "per_device_train_batch_size": 2,
  "gradient_accumulation_steps": 8,
  "effective_batch_size": 16,
  "fp16": true,
  "gradient_checkpointing": true,
  "weight_decay": 0.01,
  "max_grad_norm": 1.0,
  "num_train_epochs": 5,
  "logging_steps": 10,
  "save_strategy": "epoch",
  "evaluation_strategy": "epoch",
  "save_total_limit": 3
}
```

---

## 4. Step-by-Step Training Execution

### Step 1: Ingest and Validate Dataset
Ensure dataset is processed and split:
```bash
python training/voice/prepare_dataset.py \
  --input_dir ./data/raw_audio \
  --output_dir ./data/processed \
  --target_sr 24000 \
  --normalize_lufs -23.0
```

### Step 2: Launch Training Script
Run `train_voice.py` pointing to the generated manifest:
```bash
python training/voice/train_voice.py \
  --config training/voice/configs/lora_pilot_config.json \
  --train_manifest ./data/processed/train_manifest.jsonl \
  --val_manifest ./data/processed/val_manifest.jsonl \
  --output_dir ./checkpoints/zara_voice_pilot_v1
```

### Step 3: Monitor Training Metrics
The script logs progress at every `logging_steps`:
```text
Epoch 1/5 | Step 80/400 | Train Loss: 2.145 | Val Loss: 2.012 | LR: 1.84e-4 | VRAM: 11.2 GB
Epoch 2/5 | Step 160/400 | Train Loss: 1.821 | Val Loss: 1.764 | LR: 1.42e-4 | VRAM: 11.2 GB
...
```

### Step 4: Resume from Interrupted Checkpoints
If a Google Colab session disconnects or a preemption occurs, `train_voice.py` automatically detects and resumes from the latest checkpoint:
```bash
python training/voice/train_voice.py \
  --resume_from_checkpoint ./checkpoints/zara_voice_pilot_v1/checkpoint-last
```

---

## 5. Artifact Export & Packaging

Once validation loss stabilizes, export the final adapter weights:
```text
checkpoints/zara_voice_pilot_v1/
├── adapter_model.safetensors      # Trained LoRA weights (~48 MB)
├── adapter_config.json           # LoRA configuration metadata
├── training_args.bin             # PyTorch serialized arguments
├── trainer_state.json            # Final loss curves and learning rate logs
└── voice_metadata.json           # Speaker identity profile, timbre notes, and tags
```
These adapter weights can then be loaded directly into `ZaraVoiceEngine` via the `ZaraLocalModelBridge` interface.
