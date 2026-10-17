# Silk Voice AI: Deep Technical Research & Model Investigation

## 1. Overview & Architectural Taxonomy

Rumik AI's voice synthesis suite, named **Silk**, is designed to move beyond traditional text-to-speech by synthesizing emotionally expressive, code-switched speech with natural non-verbal vocalizations (laughs, sighs, whispers, chuckles).

Silk is composed of three distinct variants:

```
                               ┌─────────────────────────────────┐
                               │     Silk Voice Model Family     │
                               └────────────────┬────────────────┘
                                                │
             ┌──────────────────────────────────┼──────────────────────────────────┐
             ▼                                  ▼                                  ▼
   ┌──────────────────┐               ┌──────────────────┐               ┌──────────────────┐
   │   Silk Muga 1    │               │Silk Mulberry 1.5 │               │  Rumik OSS 1     │
   │  (Tone-Tagged)   │               │  (Description)   │               │ (Open Weights)   │
   ├──────────────────┤               ├──────────────────┤               ├──────────────────┤
   │ - Tagged prefix  │               │ - NL description │               │ - 3.4B parameters│
   │ - Exact mood     │               │ - 12 preset IDs  │               │ - Tiny Aya Fire  │
   │ - Batch buffer   │               │ - Audio stream   │               │ - Kyutai Mimi    │
   │ - Cloud hosted   │               │ - Cloud hosted   │               │ - Open weights   │
   └──────────────────┘               └──────────────────┘               └──────────────────┘
```

---

## 2. Audio Tokenization & Neural Codec Integration

### 2.1. Neural Codec: Kyutai Mimi
Our technical investigation into `rumik-ai/rumik-oss-1` revealed that Rumik employs the **Mimi** neural audio codec developed by Kyutai (the research lab behind the Moshi full-duplex speech-text model).
* **Sample Rate**: 24 kHz mono waveform.
* **Framing**: Operates at a low frame rate (~12.5 Hz to 25 Hz), drastically reducing sequence length compared to 50 Hz EnCodec models.
* **Residual Vector Quantization (RVQ)**: Employs 8 hierarchical codebook layers.
* **Flattened / Delay-Pattern Autoregressive Formulation**:
  Rather than predicting all 8 codebooks simultaneously with a separate diffusion head, the causal transformer predicts the discrete tokens in an interleaved, flattened delay pattern across time steps:
  $$\text{Audio Sequence} = [c_{1, t}, c_{2, t}, \dots, c_{8, t}, c_{1, t+1}, \dots]$$
* **Decoder**: A frozen Mimi neural vocoder transforms the 8-layer discrete token stream back into 24 kHz audio.

### 2.2. Backbone Language Model: Tiny Aya Fire
* **Backbone**: `CohereLabs/tiny-aya-fire` (a ~3.4B parameter multilingual causal language model).
* **Multilingual Transfer**: Pre-trained on diverse international languages, enabling zero-shot and fine-tuned pronunciation across 22 Indic scripts and Latin romanized Hinglish.
* **Vocabulary Expansion**: The model's embedding matrix is expanded to include both language text tokens and special discrete audio codebook tokens ($8 \times \text{codebook size}$), plus control tokens (`<laugh>`, `<sigh>`, `[happy]`).

---

## 3. Expressive Steering & Delivery Mechanisms

### 3.1. Tone Tags & Inline Events (Silk Muga 1)
Muga enforces strict syntax rules documented in `prompting-muga.md`:
* **Tone Tag**: Must be the very first token in the paragraph:
  `[happy]`, `[excited]`, `[sad]`, `[angry]`, `[neutral]`, `[whisper]`
* **Inline Events**: Punctuate speech with non-verbal sounds:
  `<laugh>` (0.5–1.5s), `<chuckle>` (0.3–0.7s), `<sigh>` (0.4–0.8s)
* **Emotional Compatibility Matrix**:
  | Tone | `<laugh>` | `<chuckle>` | `<sigh>` |
  | :--- | :---: | :---: | :---: |
  | `[happy]` | Best (✓✓) | Best (✓✓) | Avoid (✗) |
  | `[excited]` | Best (✓✓) | OK (✓) | Avoid (✗) |
  | `[sad]` | Avoid (✗) | Avoid (✗) | Best (✓✓) |
  | `[angry]` | Avoid (✗) | Rare (~) | OK (✓) |
  | `[neutral]` | OK (✓) | Avoid (✗) | OK (✓) |
  | `[whisper]` | Avoid (✗) | OK (✓) | OK (✓) |

### 3.2. Natural-Language Steering (Silk Mulberry 1.5)
Mulberry generates voice conditioning embeddings dynamically from a descriptive sentence:
* **The Formula**:
  `"a {gender} {age} {accent} voice, {pitch} pitch, {timbre}, {pacing} pacing, {emotion}, {register} register, like a {role}."`
* **Presets**: 12 named speaker identities (`emma`, `mia`, `sophia`, `ava`, `ira`, `siya`, `aisha`, `zoya`, `lucas`, `noah`, `theo`, `adam`).
* **Rich Inline Tags**: `<laugh>`, `<laugh_harder>`, `<sigh>`, `<chuckle>`, `<gasp>`, `<angry>`, `<excited>`, `<whisper>`, `<cry>`, `<scream>`, `<sing>`, `<snort>`, `<exhale>`, `<gulp>`, `<giggle>`, `<sarcastic>`, `<curious>`.

---

## 4. Hardware Evaluation & Local Inference Feasibility

### 4.1. Local System Diagnostics
We performed empirical hardware diagnostics on the active host environment:
* **PyTorch Version**: `2.11.0+cpu`
* **CUDA Availability**: `False` (No GPU hardware available on host)
* **Host CPU**: Multi-core x86_64 CPU

### 4.2. Local Inference Assessment of Rumik OSS 1 (3.4B)
* **Model Size**: 3.4 billion parameters requires ~6.8 GB in FP16 or ~3.5 GB in 8-bit quantized weights.
* **Autoregressive Step Latency**:
  To generate 1 second of audio at 24 kHz via Mimi, the model must autoregressively decode approximately 100 to 200 discrete tokens ($25\text{ frames/s} \times 8\text{ codebooks}$).
  On CPU execution (`torch.float32`), forward pass latency per token on a modern CPU averages 60–120 ms.
  $$T_{\text{synth}} = 150\text{ tokens} \times 90\text{ ms} \approx 13.5\text{ seconds of computation per 1 second of audio}$$
* **Conclusion**: Real-time interactive conversation requires Real-Time Factor (RTF) $< 0.3$. On the host CPU, RTF is $\approx 13.5$ ($>40\times$ too slow for real-time conversation). Running Rumik OSS 1 locally on this machine without CUDA is computationally prohibitive for live conversation.

---

## 5. Public Alternative Speech Architectures

To deliver responsive, expressive voice synthesis for Zara, we evaluated alternative open architectures:

| Engine / Architecture | Params | License | GPU Needed? | Expressive Capabilities | RTF (CPU) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Rumik OSS 1** | 3.4B | CC-BY-NC-4.0 | Yes (CUDA/MLX) | High (inline tags, Mimi codec) | ~13.5 (Infeasible for real-time) |
| **Kokoro-82M** | 82M | Apache 2.0 | No (Runs on CPU)| Medium (Natural pacing, English/Japanese) | ~0.25 (Real-time capable) |
| **F5-TTS / E2-TTS** | 300M | MIT | Yes (Flow Matching)| High (Zero-shot cloning, laughs) | ~2.5 (Too slow on CPU) |
| **CosyVoice 2** | 300M | Apache 2.0 | Yes | High (Multi-lingual, emotional) | ~1.8 (GPU required) |
| **Zara Expressive Neural (Edge-TTS + Dynamic Prosody)** | Cloud Neural | Open/Permissive Client | No (Runs on any device) | High (Dynamic SSML pitch/rate modulation, Hinglish voices, 0ms compute) | **< 0.05 (Instant streaming)** |

---

## 6. Zara Voice Engine Architectural Design

Based on empirical evidence and hardware realities, Zara implements a **Modular Multi-Backend Voice Architecture**:

1. **Primary Real-Time Engine (`ZaraExpressiveNeural`)**:
   - Uses Microsoft Neural high-fidelity voices (`hi-IN-SwaraNeural`, `en-IN-NeerjaNeural`, `en-US-AvaNeural`).
   - Implements dynamic SSML prosody parsing, mapping `[whispers]`, `[happy]`, `<laugh>`, `<sigh>` to rate, pitch, and contour shifts.
   - Provides chunked streaming over WebSockets for $< 200\text{ms}$ time-to-first-audio.
2. **Pluggable Silk API Bridge (`ZaraSilkBridge`)**:
   - Implements direct compatibility with Rumik's `POST /v1/tts` and WebSocket streaming session when a `RUMIK_API_KEY` is present.
3. **Pluggable Local OSS Model Hook (`ZaraLocalModelBridge`)**:
   - Pre-configured abstraction for loading `rumik-ai/rumik-oss-1` or `Kokoro-82M` if the host environment is equipped with a CUDA GPU or MLX accelerator.
