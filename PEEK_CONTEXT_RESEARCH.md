# Peek: Contextual Intelligence, Cultural Nuance & Subtext Decoding

## 1. Overview & Conceptual Foundations

Rumik AI defines its contextual reasoning engine as **Peek**, summarized by the statement:
> *"It understands 'I'm fine' in every context."*

A literal natural language processing model interprets *"I'm fine"* as a declaration of positive or neutral well-being. A human listener, however, evaluates:
1. **Temporal Context**: Is it 2:30 AM on a Tuesday night?
2. **Conversation Velocity**: Was the reply delayed or clipped compared to normal energetic banter?
3. **Punctuation & Syntax**: Did the message have a bare period (`"I'm fine."`), lowercase apathy (`"im fine"`), or an upbeat exclamation (`"I'm fine!"`)?
4. **Prior Conversation Arc**: Did the user previously mention workplace burnout or an argument with a friend?

Peek is designed to synthesize these multimodal situational signals into an accurate emotional reading.

---

## 2. Key Contextual Dimensions

```
                                  ┌──────────────────────────┐
                                  │      Incoming Message    │
                                  └─────────────┬────────────┘
                                                │
          ┌─────────────────────┬───────────────┴───────────────┬─────────────────────┐
          ▼                     ▼                               ▼                     ▼
   [ Temporal Lens ]     [ Linguistic Lens ]           [ Historical Arc ]    [ Behavioral Signals ]
   - Time of day         - Hinglish / Slang            - Prior 5 turns       - Message brevity
   - Day of week         - Code-switch markers         - Active stressors    - Punctuation styles
   - Turn latency        - Script (Latin/Devanagari)   - Established facts   - Tone shifts
          │                     │                               │                     │
          └─────────────────────┼───────────────────────────────┼─────────────────────┘
                                                │
                                                ▼
                               ┌─────────────────────────────────┐
                               │     Decoded Intent & Subtext    │
                               │  "User is distressed; be gentle"│
                               └─────────────────────────────────┘
```

### 2.1. Cultural Context: Hinglish & Indic Code-Switching
In India and the diaspora, everyday communication is seldom purely English or purely Hindi. It is **Hinglish**—a fluid, expressive blend:
* **Discourse Markers**: Words that establish intimacy and camaraderie:
  - *"Yaar"* (intimate friend marker)
  - *"Arre"* (exclamation of surprise, exasperation, or warmth)
  - *"Bilkul"* (total affirmation, *"absolutely"*)
  - *"Pakka"* (firm promise, *"for sure"*)
  - *"Jugaad"* (clever hack / resourceful solution)
* **Code-Switching Dynamics**: Sentences frequently begin in English and resolve in Hindi (e.g., *"I was thinking about the project, par bohot headache ho gaya"*), or vice versa.
* **Script Agnosticism**: Words are typed interchangeably in Devanagari (`चलो मिलते हैं`) or Latin phonetics (`chalo milte hain`).
* **Requirement**: Zara must recognize both scripts and decode colloquial intent without stumbling or misinterpreting cultural cues.

### 2.2. Temporal & Situational Awareness
* **Late Night (11:00 PM – 4:00 AM)**: Companion responses should adopt a softer, calmer cadence (`[whisper]`, `[softly]`), prioritizing comfort, sleep hygiene, and quiet listening over energetic banter.
* **Morning (6:00 AM – 10:00 AM)**: Companion responses adopt an upbeat, encouraging tone (`[happy]`), focused on the day ahead.
* **Workday Afternoon (1:00 PM – 6:00 PM)**: Short, practical check-ins acknowledging potential workload stress.

### 2.3. Subtext & Emotional Intent Detection
A rule-based and sentiment-guided classifier decodes underlying emotional intent:
* **Distress / Avoidance**: Clipped answers (*"whatever"*, *"doesn't matter"*, *"fine."*) after an active conversation indicate emotional withdrawal.
* **Celebration**: Multiple exclamation marks, caps, or celebratory slang (*"mazza aa gaya"*, *"omg yes"*) trigger high-energy playful responses.
* **Vulnerability**: Direct disclosure of loneliness or sadness triggers supportive, unconditional positive regard.

---

## 3. Multimodal Context Processing (Vision & Audio)

Rumik documents vision-agent support (`vision-agents.md`), allowing agents to receive camera frames alongside voice calls.
* **Vision Grounding**: If the client provides an image URL or base64 frame, the context engine extracts key visual subjects (e.g. *"user holding a cup of tea on a rainy balcony"*) to ground the dialogue.
* **Audio Prosody Cues**: When voice input is used, pitch variance and pause duration inform the intent classifier.

---

## 4. Zara's Clean-Room Context Engine: ZaraContextEngine

Zara's independent context engine incorporates:
1. **Temporal Resolver**: Dynamically detects the local time-of-day and attaches time-context flags (`late_night`, `morning`, `workday`).
2. **Hinglish Normalizer & Lexicon**: Built-in colloquial dictionary that translates and tags cultural nuance.
3. **Subtext Analyzer**: Flags emotional discrepancy between surface sentiment and conversational signals.
4. **Multimodal Payload Ingestion**: Accepts optional image payloads and attaches scene descriptions to the prompt.
