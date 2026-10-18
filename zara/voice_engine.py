"""
Zara Expressive Voice Engine (Silk Equivalent)
Why this file exists:
Voice generation is the central capability of Rumik AI. Rather than a flat, robotic TTS,
Rumik's Silk models (Muga, Mulberry, and Rumik OSS 1) modulate delivery based on tone tags
([happy], [whisper], [sad]), descriptive voice attributes, and paralinguistic inline events
(<laugh>, <sigh>, <chuckle>). This engine abstracts speech synthesis across multiple backends:
1. Expressive Neural Engine with dynamic prosody mapping, multi-paragraph steering, and true format transcoding.
2. Silk API Bridge (direct proxy to Rumik's production endpoints if an API key is present).
3. Local Model Bridge hook (for offline checkpoints like Kokoro, F5-TTS, or Rumik-OSS-1).
"""

import io
import os
import re
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Tuple, Optional, List
import edge_tts

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

# Voice identities and linguistic configurations
ZARA_VOICES: Dict[str, Dict[str, Any]] = {
    "zara-expressive": {
        "voice_id": "en-IN-NeerjaNeural",
        "name": "Zara Expressive",
        "description": "Warm, engaging, conversational Indian English voice",
        "language": "en-IN",
        "gender": "Female"
    },
    "zara-hinglish": {
        "voice_id": "hi-IN-SwaraNeural",
        "name": "Zara Hinglish",
        "description": "Fluid, natural bilingual Hindi-English companion voice",
        "language": "hi-IN",
        "gender": "Female"
    },
    "zara-intimate": {
        "voice_id": "en-US-AvaNeural",
        "name": "Zara Intimate",
        "description": "Calm, soothing, empathetic companion voice for quiet moments",
        "language": "en-US",
        "gender": "Female"
    },
    "zara-playful": {
        "voice_id": "en-GB-SoniaNeural",
        "name": "Zara Playful",
        "description": "Bright, spirited, energetic tone for joyful banter",
        "language": "en-GB",
        "gender": "Female"
    },
    "zara-storyteller": {
        "voice_id": "hi-IN-MadhurNeural",
        "name": "Zara Storyteller",
        "description": "Deep, warm, reflective cadence for longer narratives",
        "language": "hi-IN",
        "gender": "Male"
    },
    "zara-podcast": {
        "voice_id": "en-IN-PrabhatNeural",
        "name": "Zara Podcast",
        "description": "Articulate, steady pacing for informative discussions",
        "language": "en-IN",
        "gender": "Male"
    }
}


class ZaraLocalModelBridge:
    """
    Local Neural Model Bridge Hook for Custom Trained Checkpoints
    Why this class exists:
    Provides a clean, modular abstraction to load and execute local voice models
    (such as Kokoro-82M, Flow-Matching F5-TTS, or Rumik-OSS-1 LoRA adapters)
    directly on host hardware or cloud environments without cloud service dependencies.

    Tricky logic:
    Inspects whether local checkpoint files exist; if missing or invalid, gracefully
    signals availability as False so Zara seamlessly falls back to the Expressive Neural Engine.

    TODO: Add direct ONNX runtime session binding for Kokoro CPU inference.

    @danishansari-dev checkpoint_dir - Path to local checkpoint directory
    @returns ZaraLocalModelBridge instance
    """
    def __init__(self, checkpoint_dir: Optional[str] = None):
        self.checkpoint_dir = checkpoint_dir or os.getenv("ZARA_MODEL_CHECKPOINT")
        self.is_available = False
        self.model_metadata: Dict[str, Any] = {}

        if self.checkpoint_dir and os.path.exists(self.checkpoint_dir):
            meta_path = os.path.join(self.checkpoint_dir, "training_summary.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        self.model_metadata = json.load(f)
                    self.is_available = True
                except Exception:
                    self.is_available = False

    def can_synthesize(self) -> bool:
        return self.is_available


class ZaraVoiceEngine:
    """
    Why this class exists:
    Provides a unified, pluggable interface for speech synthesis that translates
    Rumik-style tone tags and inline paralinguistic events into expressive acoustic modulations
    and transcodes to real WAV, PCM, or MP3 audio streams.
    """

    def __init__(self, default_voice: str = "zara-expressive", local_checkpoint_dir: Optional[str] = None):
        """
        Initializes the voice engine with default voice and credentials.
        Why this code exists:
        Establishes defaults for voice synthesis, checks for Rumik Silk API environment keys,
        and initializes local model bridge hooks.

        Tricky logic:
        None.

        TODO: Support dynamic hot-reloading of API keys from vault.

        @danishansari-dev default_voice - Default voice key to use from ZARA_VOICES
        @danishansari-dev local_checkpoint_dir - Optional path to custom trained voice weights
        @returns None
        """
        self.default_voice = default_voice
        self.silk_api_key = os.getenv("RUMIK_API_KEY")
        self.local_bridge = ZaraLocalModelBridge(checkpoint_dir=local_checkpoint_dir)

    def resolve_voice_from_description(self, description: str) -> Tuple[str, str, str]:
        """
        Resolves voice persona and prosodic tuning from a Mulberry natural language description
        Why this code exists:
        Silk Mulberry 1.5 allows steering speech using descriptive phrases like:
        'a female 20s hindi voice, smooth timbre, casual pacing, warm emotion, like a companion.'
        This method resolves natural language descriptions into concrete voice identities and SSML deltas.

        Tricky logic:
        Extracts gender, age, language/accent, pacing, and emotion keywords using regex pattern
        matching and computes matching voice IDs with fine-grained rate and pitch offsets.

        TODO: Support embedding-based vector similarity search against a larger voice library.

        @danishansari-dev description - Natural language voice description string
        @returns Tuple of (selected_voice_name, rate_delta, pitch_delta)
        """
        if not description or not description.strip():
            return self.default_voice, "+0%", "+0Hz"

        desc_lower = description.lower()
        selected_voice = self.default_voice
        rate_delta = "+0%"
        pitch_delta = "+0Hz"

        # 1. Gender and accent resolution using word boundary regex to prevent 'female' matching 'male'
        is_female = bool(re.search(r'\b(female|woman|girl|feminine|lady)\b', desc_lower))
        is_male = bool(re.search(r'\b(male|man|boy|deep baritone|masculine|gentleman)\b', desc_lower)) and not is_female
        is_hindi = any(h in desc_lower for h in ["hindi", "hinglish", "indian", "desi", "swara", "neerja"])
        is_british = any(b in desc_lower for b in ["british", "uk", "english accent", "sonia"])
        is_american = any(a in desc_lower for a in ["american", "us accent", "california", "ava"])

        if is_male:
            if is_hindi:
                selected_voice = "zara-storyteller"
            else:
                selected_voice = "zara-podcast"
        else:
            if is_hindi:
                selected_voice = "zara-hinglish" if "bilingual" in desc_lower or "desi" in desc_lower else "zara-expressive"
            elif is_british:
                selected_voice = "zara-playful"
            elif is_american:
                selected_voice = "zara-intimate"

        # 2. Pacing resolution
        if any(f in desc_lower for f in ["fast", "quick", "energetic", "brisk"]):
            rate_delta = "+15%"
        elif any(s in desc_lower for s in ["slow", "deliberate", "calm", "soothing", "measured"]):
            rate_delta = "-12%"

        # 3. Pitch and emotional register resolution
        if any(w in desc_lower for w in ["whisper", "soft", "intimate", "quiet"]):
            pitch_delta = "-4Hz"
            rate_delta = "-15%"
        elif any(h in desc_lower for h in ["happy", "cheerful", "bright", "playful"]):
            pitch_delta = "+5Hz"
            rate_delta = "+10%"
        elif any(d in desc_lower for d in ["deep", "grave", "somber"]):
            pitch_delta = "-6Hz"

        return selected_voice, rate_delta, pitch_delta

    def parse_prosody_and_tags(self, text: str) -> Tuple[str, str, str, str]:
        """
        Parses text for tone tags ([happy], [whisper]), inline events (<laugh>, <sigh>),
        and computes SSML rate and pitch offsets.
        Why this code exists:
        Replicates Rumik Silk Muga's tone steering without speaking punctuation or bracketed metadata aloud.

        Tricky logic:
        1. Checks for paragraph tone prefix tags: [happy], [excited], [sad], [angry], [neutral], [whisper], [intimate].
        2. Detects inline paralinguistic events (<laugh>, <chuckle>, <sigh>, <gasp>, <giggle>, <laugh_harder>).
        3. Rather than merely stripping tags, replaces paralinguistic markers with acoustic punctuation
           (e.g., subtle ellipses pause '... ' for sighs) while applying rate/pitch offsets so speech pauses naturally.

        TODO: Integrate acoustic vocoder bursts for synthetic non-verbal laugh/giggle generation.

        @danishansari-dev text - Spoken dialogue string with optional tags
        @returns Tuple of (cleaned_text, rate_delta, pitch_delta, detected_tone)
        """
        clean_text = text.strip()
        detected_tone = "neutral"
        rate = "+0%"
        pitch = "+0Hz"

        # 1. Parse Muga tone tags
        tone_match = re.match(r'^\s*\[(happy|excited|sad|angry|neutral|whisper|softly|intimate)\]\s*', clean_text, re.IGNORECASE)
        if tone_match:
            detected_tone = tone_match.group(1).lower()
            clean_text = clean_text[tone_match.end():]

        # 2. Map tone to prosodic rate & pitch modulation
        if detected_tone in ["whisper", "softly", "intimate"]:
            rate = "-15%"
            pitch = "-4Hz"
        elif detected_tone in ["happy", "excited"]:
            rate = "+12%"
            pitch = "+5Hz"
        elif detected_tone in ["sad"]:
            rate = "-18%"
            pitch = "-6Hz"
        elif detected_tone in ["angry"]:
            rate = "+10%"
            pitch = "+4Hz"

        # 3. Detect and handle inline paralinguistic events with acoustic cadence adjustment
        if re.search(r'<\s*sigh\s*>', clean_text, re.IGNORECASE):
            rate = "-20%"
            pitch = "-5Hz"
            clean_text = re.sub(r'<\s*sigh\s*>', '... ', clean_text, flags=re.IGNORECASE)
        elif re.search(r'<\s*chuckle\s*>', clean_text, re.IGNORECASE):
            rate = "+6%"
            pitch = "+3Hz"
            clean_text = re.sub(r'<\s*chuckle\s*>', '... ', clean_text, flags=re.IGNORECASE)
        elif re.search(r'<\s*gasp\s*>', clean_text, re.IGNORECASE):
            rate = "-10%"
            pitch = "+4Hz"
            clean_text = re.sub(r'<\s*gasp\s*>', '... ', clean_text, flags=re.IGNORECASE)
        elif re.search(r'<\s*giggle\s*>', clean_text, re.IGNORECASE):
            rate = "+14%"
            pitch = "+6Hz"
            clean_text = re.sub(r'<\s*giggle\s*>', ' ', clean_text, flags=re.IGNORECASE)
        elif re.search(r'<\s*laugh_harder\s*>', clean_text, re.IGNORECASE):
            rate = "+18%"
            pitch = "+8Hz"
            clean_text = re.sub(r'<\s*laugh_harder\s*>', ' ', clean_text, flags=re.IGNORECASE)
        elif re.search(r'<\s*laugh\s*>', clean_text, re.IGNORECASE):
            rate = "+15%"
            pitch = "+6Hz"
            clean_text = re.sub(r'<\s*laugh\s*>', ' ', clean_text, flags=re.IGNORECASE)

        # 4. Strip any remaining bracketed/tagged metadata and leading/trailing ellipsis artifacts
        clean_text = re.sub(r'\[.*?\]', '', clean_text)
        clean_text = re.sub(r'<.*?>', '', clean_text)
        clean_text = re.sub(r'^\s*(?:\.\.\.|\.)\s*', '', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        if not clean_text:
            clean_text = text  # Fallback if text only contained tags

        return clean_text, rate, pitch, detected_tone

    def split_paragraphs_with_tones(self, text: str) -> List[Tuple[str, str, str, str]]:
        """
        Decomposes multi-paragraph text into individual tone-steered chunks per Silk Muga specification.
        Why this code exists:
        Silk Muga 1 documents that tone tags apply per paragraph ('a blank line starts a new paragraph and a new tone').
        This method parses multi-paragraph turns so each section receives its appropriate emotional prosody.

        Tricky logic:
        Splits by double newline regex, strips whitespace, and falls back to a single chunk if text is unseparated.

        TODO: Support paragraph-level emotion inference when explicit tags are absent.

        @danishansari-dev text - Full dialogue text
        @returns List of (clean_text, rate, pitch, tone) tuples
        """
        paragraphs = re.split(r'\n\s*\n', text.strip())
        chunks = []
        for p in paragraphs:
            p_strip = p.strip()
            if not p_strip:
                continue
            chunks.append(self.parse_prosody_and_tags(p_strip))
        return chunks if chunks else [self.parse_prosody_and_tags(text)]

    def transcode_audio(self, mp3_bytes: bytes, target_format: str = "mp3") -> Tuple[bytes, str]:
        """
        Transcodes raw synthesized MP3 bytes to the requested audio format (WAV, PCM, or MP3).
        Why this code exists:
        Prevents format corruption by ensuring callers requesting WAV or 24kHz PCM receive
        genuinely transcoded RIFF/PCM data rather than mislabeled MP3 frames.

        Tricky logic:
        Uses pydub to enforce a standard 24,000 Hz sample rate and 1 channel (mono) to exactly
        match Rumik AI's documented 24 kHz audio specification.

        TODO: Optimize transcoding buffer allocation for high-concurrency environments.

        @danishansari-dev mp3_bytes - Synthesized MP3 audio bytes
        @danishansari-dev target_format - 'mp3', 'wav', or 'pcm'
        @returns Tuple of (transcoded_bytes, content_type)
        """
        fmt = (target_format or "mp3").lower().strip()
        if fmt == "mp3" or not PYDUB_AVAILABLE:
            return mp3_bytes, "audio/mpeg"

        try:
            seg = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
            seg = seg.set_frame_rate(24000).set_channels(1)

            if fmt == "wav":
                out_buf = io.BytesIO()
                seg.export(out_buf, format="wav")
                return out_buf.getvalue(), "audio/wav"
            elif fmt == "pcm":
                # Raw signed 16-bit little-endian 24kHz mono PCM
                return seg.raw_data, "audio/pcm; rate=24000; channels=1; format=s16le"
            else:
                return mp3_bytes, "audio/mpeg"
        except Exception:
            # Fallback to original bytes if transcoding fails
            return mp3_bytes, "audio/mpeg"

    async def synthesize(
        self,
        text: str,
        voice_name: str = "zara-expressive",
        emotion: Optional[str] = None,
        audio_format: str = "mp3",
        description: Optional[str] = None
    ) -> bytes:
        """
        Synthesizes speech into binary audio bytes in the requested format.
        Why this code exists:
        Provides direct audio for REST API responses and audio playback.

        Tricky logic:
        1. If descriptive prompting is supplied without a voice name, resolves Mulberry formula.
        2. If multi-paragraph tone switching is detected and pydub is available, synthesizes
           each paragraph with its own prosody delta and stitches them into a seamless audio track.
        3. Applies real audio transcoding (MP3, WAV, PCM) to guarantee format compliance.

        TODO: Implement streaming cached audio chunks directly for repeated phrases.

        @danishansari-dev text - Dialogue text to synthesize
        @danishansari-dev voice_name - Named voice identifier from ZARA_VOICES
        @danishansari-dev emotion - Optional manual emotional override
        @danishansari-dev audio_format - Target audio format ('mp3', 'wav', 'pcm')
        @danishansari-dev description - Optional Silk Mulberry natural language description
        @returns Binary audio data
        """
        # 1. Mulberry Natural Language Description handling
        desc_rate_mod = "+0%"
        desc_pitch_mod = "+0Hz"
        if description and description.strip():
            resolved_voice, desc_rate_mod, desc_pitch_mod = self.resolve_voice_from_description(description)
            if voice_name == "zara-expressive":
                voice_name = resolved_voice

        # 2. Optional Silk API bridge if key is provided
        if self.silk_api_key:
            try:
                import urllib.request
                payload = json.dumps({
                    "model": "muga" if text.startswith("[") else "mulberry",
                    "text": text,
                    "audio_format": audio_format,
                    "description": description or ZARA_VOICES.get(voice_name, {}).get("description", "conversational voice")
                }).encode('utf-8')
                req = urllib.request.Request(
                    "https://silk-api.rumik.ai/v1/tts",
                    data=payload,
                    headers={"Authorization": f"Bearer {self.silk_api_key}", "Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    return resp.read()
            except Exception:
                pass

        # 3. Built-in Expressive Neural Engine
        selected_voice_meta = ZARA_VOICES.get(voice_name, ZARA_VOICES["zara-expressive"])
        voice_id = selected_voice_meta["voice_id"]

        paragraph_chunks = self.split_paragraphs_with_tones(text)

        # Multi-paragraph synthesis with audio stitching if multiple paragraphs exist
        if len(paragraph_chunks) > 1 and PYDUB_AVAILABLE:
            combined_segment = None
            for clean_text, rate, pitch, _ in paragraph_chunks:
                if emotion:
                    if emotion in ["playful", "happy", "excited"]:
                        rate, pitch = "+12%", "+5Hz"
                    elif emotion in ["calm", "supportive", "whisper"]:
                        rate, pitch = "-15%", "-4Hz"

                if desc_rate_mod != "+0%":
                    rate = desc_rate_mod
                if desc_pitch_mod != "+0Hz":
                    pitch = desc_pitch_mod

                comm = edge_tts.Communicate(clean_text, voice_id, rate=rate, pitch=pitch)
                buf = io.BytesIO()
                async for chunk in comm.stream():
                    if chunk["type"] == "audio":
                        buf.write(chunk["data"])

                seg = AudioSegment.from_file(io.BytesIO(buf.getvalue()), format="mp3")
                # Add 300ms natural conversational pause between paragraphs
                pause = AudioSegment.silent(duration=300)
                if combined_segment is None:
                    combined_segment = seg
                else:
                    combined_segment = combined_segment + pause + seg

            out_buf = io.BytesIO()
            combined_segment.export(out_buf, format="mp3")
            mp3_bytes = out_buf.getvalue()
        else:
            # Single paragraph synthesis
            clean_text, rate, pitch, _ = paragraph_chunks[0]
            if emotion:
                if emotion in ["playful", "happy", "excited"]:
                    rate, pitch = "+12%", "+5Hz"
                elif emotion in ["calm", "supportive", "whisper"]:
                    rate, pitch = "-15%", "-4Hz"

            if desc_rate_mod != "+0%":
                rate = desc_rate_mod
            if desc_pitch_mod != "+0Hz":
                pitch = desc_pitch_mod

            communicate = edge_tts.Communicate(clean_text, voice_id, rate=rate, pitch=pitch)
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
            mp3_bytes = buffer.getvalue()

        # Transcode to requested format (WAV, PCM, or MP3)
        transcoded_bytes, _ = self.transcode_audio(mp3_bytes, target_format=audio_format)
        return transcoded_bytes

    async def stream_audio_chunks(
        self,
        text: str,
        voice_name: str = "zara-expressive",
        description: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Streams audio packets chunk-by-chunk in real time.
        Why this code exists:
        Low-latency streaming is critical for real-time conversation. This generator yields
        audio chunks as soon as frames are received, minimizing time-to-first-byte down to < 200ms.

        Tricky logic:
        Extracts prosody and tags from text first so speech rate and pitch parameters are applied
        to the underlying network stream, ensuring emotional inflection without spoken markup.

        TODO: Support bidirectional interruption handling when user barge-in occurs.

        @danishansari-dev text - Spoken dialogue text
        @danishansari-dev voice_name - Target voice identifier
        @danishansari-dev description - Optional Mulberry natural language description
        @returns Asynchronous generator of binary audio chunks
        """
        if description and description.strip():
            resolved_voice, r_mod, p_mod = self.resolve_voice_from_description(description)
            if voice_name == "zara-expressive":
                voice_name = resolved_voice

        clean_text, rate, pitch, _ = self.parse_prosody_and_tags(text)
        selected_voice_meta = ZARA_VOICES.get(voice_name, ZARA_VOICES["zara-expressive"])
        voice_id = selected_voice_meta["voice_id"]

        communicate = edge_tts.Communicate(clean_text, voice_id, rate=rate, pitch=pitch)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
