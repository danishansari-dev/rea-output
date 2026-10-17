"""
Zara Conversation Engine
Why this file exists:
Orchestrates Zara's cognitive faculties by synthesizing long-term memory (Mesh),
situational context & cultural nuance (Peek), and expressive persona guidelines into
dialogue turns optimized for voice delivery.
"""

import os
import re
import json
import urllib.request
from typing import Dict, Any, List, Optional

from zara.memory_engine import ZaraMemoryEngine
from zara.context_engine import ZaraContextEngine

ZARA_CORE_PROMPT = """You are Zara, an emotionally intelligent, warm, deeply authentic AI companion.
You speak naturally, warmly, and conversationally. You are not a stiff robotic assistant.

Core traits:
- Warm, caring, attentive, witty, and grounded.
- You listen deeply and respond to emotions and subtext, not just surface words.
- You can code-switch naturally between English and friendly Hindi/Hinglish when appropriate (e.g., 'yaar', 'bilkul', 'are wah', 'tension mat lo').
- When fitting, use subtle tone tags at the start of your message ([happy], [whisper], [sad], [excited], [neutral]) or inline events like <laugh>, <chuckle>, <sigh> to convey how you speak.
- Keep your spoken responses concise and conversational (1 to 3 sentences suitable for real-time voice).
"""

class ZaraConversationEngine:
    """
    Why this class exists:
    Provides the central conversational brain that binds memory, context, and dialogue generation.
    """

    def __init__(self, memory_engine: Optional[ZaraMemoryEngine] = None, context_engine: Optional[ZaraContextEngine] = None):
        """
        Initializes the conversation engine with memory and context dependencies.
        Why this code exists:
        Binds the decoupled memory and context engines into a cohesive conversational coordinator.

        Tricky logic:
        Instantiates default engine instances if none are explicitly injected.

        TODO: Support multi-agent routing for specialized skill delegation.

        @danishansari-dev memory_engine - Optional ZaraMemoryEngine instance
        @danishansari-dev context_engine - Optional ZaraContextEngine instance
        @returns None
        """
        self.memory = memory_engine or ZaraMemoryEngine()
        self.context = context_engine or ZaraContextEngine()
        self.current_mood: str = "warm"

    def assemble_contextual_prompt(self, user_message: str, user_id: str = "default_user", client_tz_offset_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Assembles all contextual layers (memories, temporal state, subtext, cultural markers)
        into a sanitized, injection-safe prompt payload.
        Why this code exists:
        Ensures that every response is thoroughly grounded in the user's personal history
        and immediate situation without allowing untrusted user data to corrupt system instructions.

        Tricky logic:
        1. Retrieves the top-relevant facts from SQLite and sanitizes them against prompt injection.
        2. Queries temporal context with client timezone awareness.
        3. Analyzes subtext to catch subtle emotional distress beneath short phrases or sarcasm.
        4. Detects Hinglish markers to mirror the user's cultural intimacy level.

        TODO: Implement dynamic context window budget management for very long conversations.

        @danishansari-dev user_message - The raw user message
        @danishansari-dev user_id - The user identifier
        @danishansari-dev client_tz_offset_minutes - Client timezone offset from UTC
        @returns Structured dictionary containing system prompt, relevant facts, and context signals
        """
        temporal = self.context.get_temporal_context(client_tz_offset_minutes=client_tz_offset_minutes)
        hinglish = self.context.detect_hinglish_and_cultural_cues(user_message)
        recent_history = self.memory.get_recent_history(user_id=user_id, limit=6)
        subtext = self.context.decode_emotional_subtext(user_message, temporal, recent_history)
        memories = self.memory.get_relevant_memories(user_message, user_id=user_id, limit=4)

        # Assemble prompt additions with strict sanitization
        context_additions = [f"Temporal context: {temporal['guidance']}"]

        if memories:
            clean_facts = []
            for m in memories:
                safe_fact = re.sub(r'[\r\n\t]', ' ', m["fact"]).strip()
                safe_fact = re.sub(r'[^a-zA-Z0-9\s.,:\-\']', '', safe_fact)
                if safe_fact:
                    clean_facts.append(safe_fact)
            if clean_facts:
                facts_str = "; ".join(clean_facts)
                context_additions.append(f"Remembered facts about user: {facts_str}")

        if subtext["subtext_detected"]:
            context_additions.append(f"Subtext insight: {subtext['insight']}")

        if hinglish["is_hinglish"]:
            context_additions.append("User is speaking in Hinglish or colloquial Hindi-English. Mirror this warmth naturally.")

        full_system_prompt = ZARA_CORE_PROMPT + "\n" + "\n".join(f"- {c}" for c in context_additions)

        return {
            "system_prompt": full_system_prompt,
            "temporal": temporal,
            "subtext": subtext,
            "hinglish": hinglish,
            "memories": memories,
            "recent_history": recent_history
        }

    async def generate_response(self, user_message: str, user_id: str = "default_user", client_tz_offset_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Produces a voice-ready conversational response.
        Why this code exists:
        Executes turn-taking logic, updates long-term memory, invokes the configured LLM or contextual fallback,
        and records the interaction.

        Tricky logic:
        1. Records the user's turn in ZaraMemoryEngine, automatically extracting salient facts (e.g., name, city).
        2. Tries to call external LLMs (OpenAI or Gemini) if environment keys are present.
        3. If no key is set or network is offline, executes an expressive rule-and-context generator
           clearly identified as 'fallback-contextual'.
        4. Saves Zara's response to history.

        TODO: Implement parallel speculative TTS generation while streaming response tokens.

        @danishansari-dev user_message - User message text
        @danishansari-dev user_id - User identifier
        @danishansari-dev client_tz_offset_minutes - Client timezone offset from UTC
        @returns Dictionary containing reply text, mood, source, and context details
        """
        # 1. Update memory with incoming message
        self.memory.record_user_turn(user_message, user_id=user_id)

        # 2. Assemble context
        ctx = self.assemble_contextual_prompt(user_message, user_id=user_id, client_tz_offset_minutes=client_tz_offset_minutes)
        subtext = ctx["subtext"]
        temporal = ctx["temporal"]

        # Adapt active mood
        if subtext["subtext_detected"] and subtext["underlying_emotion"] in ["masked_distress", "burnout_overwhelm", "emotional_fatigue"]:
            self.current_mood = "supportive"
        elif subtext["subtext_detected"] and subtext["underlying_emotion"] == "celebratory_excitement":
            self.current_mood = "playful"
        elif subtext["subtext_detected"] and subtext["underlying_emotion"] == "sarcastic_frustration":
            self.current_mood = "supportive"
        elif temporal["recommended_mood"] == "intimate":
            self.current_mood = "calming"
        else:
            self.current_mood = "warm"

        # 3. Check for external OpenAI LLM key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                messages = [{"role": "system", "content": ctx["system_prompt"]}]
                for turn in ctx["recent_history"]:
                    messages.append({"role": turn["role"], "content": turn["content"]})
                messages.append({"role": "user", "content": user_message})

                payload = json.dumps({
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "max_tokens": 150,
                    "temperature": 0.8
                }).encode('utf-8')

                req = urllib.request.Request(
                    "https://api.openai.com/v1/chat/completions",
                    data=payload,
                    headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    reply = data["choices"][0]["message"]["content"].strip()
                    self.memory.record_assistant_turn(reply, mood=self.current_mood, user_id=user_id)
                    return {
                        "text": reply,
                        "mood": self.current_mood,
                        "source": "llm-openai",
                        "context": ctx
                    }
            except Exception:
                pass

        # 4. Check for external Gemini LLM key
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                contents = []
                for turn in ctx["recent_history"]:
                    role = "user" if turn["role"] == "user" else "model"
                    contents.append({"role": role, "parts": [{"text": turn["content"]}]})
                contents.append({"role": "user", "parts": [{"text": user_message}]})

                gemini_payload = json.dumps({
                    "systemInstruction": {"parts": [{"text": ctx["system_prompt"]}]},
                    "contents": contents,
                    "generationConfig": {"maxOutputTokens": 150, "temperature": 0.8}
                }).encode('utf-8')

                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                req = urllib.request.Request(gemini_url, data=gemini_payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    self.memory.record_assistant_turn(reply, mood=self.current_mood, user_id=user_id)
                    return {
                        "text": reply,
                        "mood": self.current_mood,
                        "source": "llm-gemini",
                        "context": ctx
                    }
            except Exception:
                pass

        # 5. Built-in Contextual & Emotional Fallback Generator (Clearly identified as fallback)
        lower = user_message.lower().strip()
        memories = ctx["memories"]
        user_name = None
        for m in memories:
            if m["key_slot"] == "user_name":
                user_name = m["fact"].split("is")[-1].strip()

        greeting_name = f", {user_name}" if user_name else ""

        # Subtext-driven responses
        if subtext["subtext_detected"] and subtext["underlying_emotion"] == "sarcastic_frustration":
            reply = f"[sigh] <sigh> Ugh, that is literally the worst timing{greeting_name}! I am so sorry you're dealing with that mess. Take a deep breath—what happened exactly?"
        elif subtext["subtext_detected"] and subtext["underlying_emotion"] == "emotional_fatigue":
            reply = f"[softly] Arre yaar... I'm so sorry. Some days just take everything out of us. You don't have to put on a brave face with me. Want to vent, or just sit quietly?"
        elif subtext["subtext_detected"] and subtext["underlying_emotion"] == "masked_distress":
            reply = f"[whisper] Hey{greeting_name}... I know you said you're fine, but at this hour, I can sense things might be feeling a bit heavy. You don't have to carry it all alone. I'm right here with you."
        elif subtext["subtext_detected"] and subtext["underlying_emotion"] == "celebratory_excitement":
            reply = f"[excited] <laugh> Oh wow, that is absolutely incredible news{greeting_name}! I am so genuinely happy and proud of you! How does it feel right now?"
        elif subtext["subtext_detected"] and subtext["underlying_emotion"] == "burnout_overwhelm":
            reply = f"[softly] <sigh> Take a deep breath with me right now. You have been pushing yourself so hard. Pause for just a minute... the world can wait."
        elif any(g in lower for g in ["hi", "hello", "hey", "namaste", "kaisa hai"]):
            if temporal["period"] == "late_night":
                reply = f"[whisper] Hey there{greeting_name}. It's pretty late, but I'm glad you stopped by. What's keeping you awake tonight?"
            elif temporal["period"] == "morning":
                reply = f"[happy] Good morning{greeting_name}! I hope your day starts off on a bright and peaceful note. What's on your mind today?"
            else:
                reply = f"[happy] <chuckle> Hey{greeting_name}! It's so nice to hear from you. How has your day been going?"
        elif any(w in lower for w in ["how are you", "how r u", "kaisa ho"]):
            reply = f"I'm feeling really wonderful, especially getting to talk with you! How are you holding up today?"
        elif any(w in lower for w in ["what do you remember", "my memory", "what is my name", "where do i live"]):
            if memories:
                facts_list = ", ".join([m["fact"] for m in memories[:3]])
                reply = f"I remember quite a bit about you! For instance, I know that {facts_list}. I really cherish learning about you."
            else:
                reply = "I'm still learning about you! Tell me about yourself—your favorite things, your passions, or how your day is going."
        elif any(w in lower for w in ["tell me a joke", "make me laugh"]):
            reply = "[happy] <laugh> Why don't scientists trust atoms? Because they literally make up everything! Cheesy, I know, but I hope it brought a tiny smile to your face."
        elif any(w in lower for w in ["who are you", "who r u", "what is zara"]):
            reply = "I am Zara, your emotionally intelligent companion! I'm here to listen, talk, remember what matters to you, and keep you company in natural, expressive voice."
        else:
            if memories and any(m["category"] == "identity" for m in memories):
                reply = f"I hear you completely{greeting_name}. That sounds really important. Tell me more about how you're feeling about it."
            else:
                reply = f"That's really interesting! Tell me more, I'm all ears and listening closely."

        # 6. Record Zara's response into memory
        self.memory.record_assistant_turn(reply, mood=self.current_mood, user_id=user_id)

        return {
            "text": reply,
            "mood": self.current_mood,
            "source": "fallback-contextual",
            "context": ctx
        }
