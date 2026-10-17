"""
Zara Context Engine (Peek Equivalent)
Why this file exists:
Rumik's 'Peek' engine is designed to understand that human language is steeped in subtext,
temporal environment, and cultural nuances. A literal NLP parser reads 'I am fine' as positive;
Peek understands that 'I am fine' spoken at 2:30 AM with a flat period carries vulnerability.
This module analyzes conversational history, temporal cues, timezone offsets, Hinglish
colloquialisms, sarcasm patterns, and multimodal inputs to decode true user intent.
"""

import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

# Hinglish colloquial markers & nuances
HINGLISH_DICTIONARY = {
    "yaar": {"meaning": "friend / intimate discourse marker", "register": "informal"},
    "arre": {"meaning": "exclamation of surprise, empathy, or exasperation", "register": "informal"},
    "bilkul": {"meaning": "absolutely / completely", "register": "affirmative"},
    "pakka": {"meaning": "definite / promised", "register": "affirmative"},
    "jugaad": {"meaning": "clever hack / workaround", "register": "cultural"},
    "tension": {"meaning": "stress / anxiety", "register": "emotional"},
    "kaisa": {"meaning": "how", "register": "inquiry"},
    "theek": {"meaning": "fine / okay", "register": "status"},
    "kya": {"meaning": "what", "register": "inquiry"},
    "bohot": {"meaning": "very / much", "register": "intensifier"},
    "sach": {"meaning": "true / really", "register": "inquiry"},
    "mazza": {"meaning": "fun / delight", "register": "positive"},
    "chal": {"meaning": "come on / let's go", "register": "informal"},
    "bhai": {"meaning": "brother / close friend", "register": "informal"},
    "mast": {"meaning": "awesome / great", "register": "positive"}
}

class ZaraContextEngine:
    """
    Why this class exists:
    Decodes subtext, temporal conditions, timezone shifts, sarcasm, and cultural nuances so
    Zara's conversational responses are profoundly context-aware rather than shallow pattern matches.
    """

    def __init__(self):
        """
        Initializes the context engine.
        Why this code exists:
        Prepares the linguistic dictionaries and temporal heuristic models.

        Tricky logic:
        None.

        TODO: Support dynamic user-specific slang dictionary customization.

        @danishansari-dev None
        @returns None
        """
        pass

    def get_temporal_context(self, client_tz_offset_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculates situational and temporal parameters adjusted for the user's local timezone.
        Why this code exists:
        Companion interactions change radically depending on whether it is late night or early morning.
        Supporting client timezone offsets guarantees users anywhere in the world receive the correct greeting.

        Tricky logic:
        If client_tz_offset_minutes is passed (e.g. +330 for IST UTC+5:30, or -300 for EST UTC-5),
        computes local time from UTC datetime. If None, falls back to server clock.

        TODO: Support daylight savings auto-detection without explicit client offsets.

        @danishansari-dev client_tz_offset_minutes - Client timezone offset from UTC in minutes
        @returns Dictionary of temporal descriptors and recommended companion register
        """
        if client_tz_offset_minutes is not None:
            tz = timezone(timedelta(minutes=client_tz_offset_minutes))
            now = datetime.now(tz)
        else:
            now = datetime.now()

        hour = now.hour

        if 23 <= hour or hour < 5:
            period = "late_night"
            recommended_mood = "intimate"
            guidance = "It is late at night. The user may be tired, lonely, or unwinding. Speak softly, gently, and warmly."
        elif 5 <= hour < 9:
            period = "morning"
            recommended_mood = "cheerful"
            guidance = "It is early morning. Speak with fresh positive energy and encourage a wonderful start to the day."
        elif 9 <= hour < 18:
            period = "workday"
            recommended_mood = "supportive"
            guidance = "It is during the workday. Keep responses concise, clear, and understanding of workplace demands."
        else:
            period = "evening"
            recommended_mood = "warm"
            guidance = "It is evening time. Encourage unwinding, sharing about how the day went, and relaxing."

        return {
            "period": period,
            "hour": hour,
            "recommended_mood": recommended_mood,
            "guidance": guidance
        }

    def detect_hinglish_and_cultural_cues(self, text: str) -> Dict[str, Any]:
        """
        Identifies Indic code-switching, Devanagari script, and colloquial markers.
        Why this code exists:
        Zara serves bilingual users who seamlessly interweave Hindi and English.
        Recognizing Hinglish allows Zara to match the user's cultural intimacy level.

        Tricky logic:
        Combines Devanagari Unicode block inspection with romanized slang token matching.

        TODO: Expand vocabulary to support South Indian loan words (e.g. 'machan', 'da').

        @danishansari-dev text - The user's input string
        @returns Analysis dict with code-switch detection and matched cultural markers
        """
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))
        tokens = re.findall(r'\b[a-zA-Z]+\b', text.lower())

        detected_slang = []
        for t in tokens:
            if t in HINGLISH_DICTIONARY:
                detected_slang.append({"token": t, **HINGLISH_DICTIONARY[t]})

        is_hinglish = has_devanagari or len(detected_slang) > 0

        return {
            "is_hinglish": is_hinglish,
            "has_devanagari": has_devanagari,
            "detected_slang": detected_slang,
            "cultural_affinity": "high" if is_hinglish else "standard"
        }

    def decode_emotional_subtext(self, text: str, temporal_context: Dict[str, Any], recent_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Decodes underlying emotional subtext, sarcasm, and cultural idioms.
        Why this code exists:
        Directly implements Rumik's 'Peek' paradigm—discerning that 'I am fine'
        at 2:00 AM indicates masked distress, and 'Oh great, my car broke down' indicates sarcasm.

        Tricky logic:
        1. Checks for sarcasm inversions: enthusiastic adjective (great, wonderful, brilliant)
           coupled with misfortune verbs/nouns (broke, crashed, canceled, failed, lost, stuck).
        2. Detects Indian colloquial mood markers (e.g., 'mood off hai').
        3. Evaluates brevity against late-night indicators for masked distress ('fine', 'nothing').

        TODO: Integrate a cross-lingual RoBERTa zero-shot sentiment classifier for nuanced literary prose.

        @danishansari-dev text - Current user message
        @danishansari-dev temporal_context - Output from get_temporal_context
        @danishansari-dev recent_history - Prior conversation turns
        @returns Dictionary containing subtext flags, apparent mood, and underlying intent
        """
        lower = text.strip().lower()

        # 1. Sarcasm detection (enthusiastic word + negative event)
        sarcasm_pattern = re.search(
            r'\b(?:oh\s+great|just\s+great|just\s+wonderful|brilliant|fantastic|awesome)\b.*?\b(?:broke|broken|crashed|died|canceled|cancelled|ruined|lost|failed|late|stuck|terrible|horrible|pain|bug|error|fired)\b',
            lower
        )
        if sarcasm_pattern:
            return {
                "subtext_detected": True,
                "underlying_emotion": "sarcastic_frustration",
                "confidence": 0.89,
                "insight": "User is using sarcastic praise to describe an annoying or stressful event. Do not celebrate; acknowledge the frustration with empathetic, lighthearted wit."
            }

        # 2. Hinglish emotional idioms (fatigue, exasperation, and relief)
        if re.search(r'\b(?:dimag\s+ka\s+dahi|dimaag\s+ka\s+dahi)\b', lower):
            return {
                "subtext_detected": True,
                "underlying_emotion": "burnout_overwhelm",
                "confidence": 0.94,
                "insight": "User expressed extreme mental exasperation ('dimag ka dahi'). Validate their intense frustration and invite them to unpack what went wrong."
            }

        if re.search(r'\b(?:scene\s+sorted|sab\s+sorted|sorted\s+hai)\b', lower):
            return {
                "subtext_detected": True,
                "underlying_emotion": "celebratory_excitement",
                "confidence": 0.91,
                "insight": "User noted things are sorted out ('scene sorted'). Celebrate their accomplishment and peace of mind!"
            }

        if re.search(r'\b(?:mood\s+off|mann\s+nahi|dimag\s+kharab|thak\s+gaya|thak\s+gayi|bohot\s+thak|bahut\s+thak|pak\s+gaya|pak\s+gayi)\b', lower):
            return {
                "subtext_detected": True,
                "underlying_emotion": "emotional_fatigue",
                "confidence": 0.92,
                "insight": "User explicitly noted their mood is down or they are deeply tired in colloquial Hinglish. Respond with gentle warmth and active listening."
            }

        # 3. The classic 'I'm fine' ambiguity
        is_fine_pattern = bool(re.match(r'^(?:i\'m fine|im fine|i am fine|all good|it\'s fine|its fine|nothing)[.!]?$', lower))
        if is_fine_pattern:
            if temporal_context.get("period") == "late_night":
                return {
                    "subtext_detected": True,
                    "underlying_emotion": "masked_distress",
                    "confidence": 0.88,
                    "insight": "User says they are fine late at night. They are likely exhausted, vulnerable, or holding something heavy. Do not press aggressively; offer gentle unconditional presence."
                }
            else:
                return {
                    "subtext_detected": True,
                    "underlying_emotion": "hesitant_reserve",
                    "confidence": 0.65,
                    "insight": "User gave a minimal 'fine' response. Acknowledge gently and invite them to share if anything is on their mind."
                }

        # 4. Burnout or overwhelmed state
        if any(w in lower for w in ["so much work", "can't do this", "exhausted", "burnout", "too much", "giving up"]):
            return {
                "subtext_detected": True,
                "underlying_emotion": "burnout_overwhelm",
                "confidence": 0.92,
                "insight": "User feels overwhelmed. Prioritize soothing validation, encourage a pause, and avoid giving unsolicited to-do lists."
            }

        # 5. Celebration and joy
        if any(w in lower for w in ["finally", "i did it", "got the job", "promoted", "won", "yay", "mazza"]):
            return {
                "subtext_detected": True,
                "underlying_emotion": "celebratory_excitement",
                "confidence": 0.90,
                "insight": "User is experiencing a genuine win. Match their excitement, celebrate enthusiastically, and reflect their joy!"
            }

        return {
            "subtext_detected": False,
            "underlying_emotion": "neutral_expressive",
            "confidence": 0.70,
            "insight": "Dialogue is conversational and direct."
        }

    def classify_conversational_intent(self, text: str) -> Dict[str, Any]:
        """
        Classifies conversational turn into primary intent and confidence.
        Why this code exists:
        Enables conversational responses to adapt their depth, pacing, and tone to the user's intent.

        Tricky logic:
        Differentiates advice-seeking questions from venting statements and memory inquiries.

        TODO: Train multi-label intent classifier for compound dialogue turns.

        @danishansari-dev text - Raw user message text
        @returns Dictionary with primary_intent, confidence, and intent_tags
        """
        lower = text.strip().lower()

        # 1. Advice seeking
        if any(w in lower for w in ["advice", "what should i do", "help me decide", "how do i handle", "what can i do", "any suggestions", "suggest me"]):
            return {
                "primary_intent": "seeking_advice",
                "confidence": 0.92,
                "intent_tags": ["advice", "guidance", "problem_solving"]
            }

        # 2. Memory inquiry
        if any(w in lower for w in ["what do you remember", "what do you know", "where do i live", "my career", "what is my name", "remember about"]):
            return {
                "primary_intent": "memory_inquiry",
                "confidence": 0.95,
                "intent_tags": ["memory", "recall", "personal_data"]
            }

        # 3. Venting
        if any(w in lower for w in ["need to vent", "just venting", "complete disaster", "worst day", "so frustrated", "can't believe this happened", "i hate everything today"]):
            return {
                "primary_intent": "venting",
                "confidence": 0.88,
                "intent_tags": ["emotional_release", "venting", "empathy_required"]
            }

        # 4. Seeking comfort / connection
        if any(w in lower for w in ["lonely", "feeling down", "miss", "sad", "hold me", "comfort", "scared"]):
            return {
                "primary_intent": "seeking_comfort",
                "confidence": 0.85,
                "intent_tags": ["comfort", "intimacy", "support"]
            }

        # 5. Greeting
        if any(lower.startswith(g) for g in ["hi", "hello", "hey", "good morning", "good evening", "namaste"]):
            return {
                "primary_intent": "greeting",
                "confidence": 0.90,
                "intent_tags": ["salutation", "start_turn"]
            }

        return {
            "primary_intent": "casual_banter",
            "confidence": 0.70,
            "intent_tags": ["conversational", "open_dialogue"]
        }

    def process_multimodal_context(self, image_data: Optional[str] = None) -> Optional[str]:
        """
        Attaches scene grounding when multimodal input (vision/image) is supplied.
        Why this code exists:
        Rumik's vision agents ground voice conversations in real-time camera views.

        Tricky logic:
        Validates presence of image_data and formats a behavioral instruction to anchor vision attention.

        TODO: Connect local CLIP/BLIP embedding model for offline image captioning.

        @danishansari-dev image_data - Image URL or base64 frame data
        @returns Formatted scene description prompt segment or None
        """
        if not image_data:
            return None
        return "User has shared an image/camera feed. Pay attention to visual surroundings and acknowledge visual elements naturally if referenced."
