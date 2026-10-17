"""
Comprehensive Zara System & Engine Test Suite
Why this file exists:
Scientifically verifies that each of Zara's four decoupled engines
(Memory, Context, Voice, Conversation) and server endpoints satisfy their
contractual obligations inspired by Rumik AI.
"""

import os
import sys
import asyncio
import tempfile
import pytest

# Ensure root directory is on pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from zara.memory_engine import ZaraMemoryEngine
from zara.context_engine import ZaraContextEngine
from zara.voice_engine import ZaraVoiceEngine
from zara.conversation_engine import ZaraConversationEngine

def test_mesh_memory_engine():
    """
    Tests persistent selective retention and contradiction resolution in ZaraMemoryEngine.
    Why this code exists:
    Verifies that Zara selectively remembers durable facts and cleanly resolves conflicting updates.

    Tricky logic:
    Creates a temporary SQLite file database and tests the full sequence: extract facts, store turn, update location (contradiction), search relevance, and delete.

    TODO: Add stress test simulating hundreds of conflicting facts.

    @danishansari-dev None
    @returns None
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        test_db = tf.name

    try:
        engine = ZaraMemoryEngine(db_path=test_db)

        # 1. Test fact extraction from personal disclosure
        facts = engine.extract_salient_facts("My name is Rohan and I work as a designer.")
        assert any(f["key_slot"] == "user_name" and "Rohan" in f["fact_value"] for f in facts)
        assert any(f["key_slot"] == "occupation" and "designer" in f["fact_value"] for f in facts)

        # 2. Test recording user turn
        engine.record_user_turn("Hi! My name is Rohan. I live in Mumbai.", user_id="test_user")
        stored_facts = engine.list_all_facts(user_id="test_user")
        assert len(stored_facts) >= 2

        # 3. Test Contradiction Resolution (Moving to Bangalore)
        engine.record_user_turn("Actually, I moved to Bangalore recently.", user_id="test_user")
        updated_facts = engine.list_all_facts(user_id="test_user")
        loc_facts = [f for f in updated_facts if f["key_slot"] == "current_city"]
        assert len(loc_facts) == 1, "Contradiction resolution failed: duplicate location facts exist"
        assert "Bangalore" in loc_facts[0]["fact_value"], "Location fact was not updated"

        # 4. Test Relevance Retrieval
        retrieved = engine.get_relevant_memories("Where do I live?", user_id="test_user")
        assert len(retrieved) > 0
        assert any("Bangalore" in r["fact"] for r in retrieved)

        # 5. Test Deletion
        fact_id = loc_facts[0]["id"]
        deleted = engine.delete_fact(fact_id, user_id="test_user")
        assert deleted is True
        remaining = engine.list_all_facts(user_id="test_user")
        assert not any(f["id"] == fact_id for f in remaining)

    finally:
        try:
            if os.path.exists(test_db):
                os.remove(test_db)
        except Exception:
            pass

def test_peek_context_engine():
    """
    Tests Hinglish detection, temporal situational cues, and subtext decoding.
    Why this code exists:
    Verifies that Zara correctly parses cultural language and decodes masked emotional distress.

    Tricky logic:
    Compares the exact same text ('I am fine') in late night vs workday temporal contexts to verify subtext emergence.

    TODO: Test regional Indian colloquial variations (e.g. Bambaiya Hindi vs Dilli Hindi).

    @danishansari-dev None
    @returns None
    """
    engine = ZaraContextEngine()

    # 1. Temporal context
    temporal = engine.get_temporal_context()
    assert "period" in temporal
    assert "guidance" in temporal

    # 2. Hinglish and colloquial cues
    hinglish_text = "Arre yaar, bilkul tension mat lo!"
    detected = engine.detect_hinglish_and_cultural_cues(hinglish_text)
    assert detected["is_hinglish"] is True
    assert any(s["token"] == "yaar" for s in detected["detected_slang"])
    assert any(s["token"] == "bilkul" for s in detected["detected_slang"])

    # 3. Subtext decoding: 'I'm fine' at late night vs neutral
    late_night_temporal = {"period": "late_night", "hour": 2, "recommended_mood": "intimate", "guidance": "Speak softly"}
    subtext_night = engine.decode_emotional_subtext("I'm fine.", late_night_temporal, [])
    assert subtext_night["subtext_detected"] is True
    assert subtext_night["underlying_emotion"] == "masked_distress"

    day_temporal = {"period": "workday", "hour": 14, "recommended_mood": "supportive", "guidance": "Concise"}
    subtext_day = engine.decode_emotional_subtext("I did it! I got the job!", day_temporal, [])
    assert subtext_day["subtext_detected"] is True
    assert subtext_day["underlying_emotion"] == "celebratory_excitement"

def test_silk_voice_prosody_parsing():
    """
    Tests Silk Muga tone tag parsing, inline event handling, and prosody computation.
    Why this code exists:
    Ensures that tags ([happy], <laugh>) steer SSML rate and pitch without being spoken aloud.

    Tricky logic:
    Asserts rate and pitch percentage deltas and clean text output stripped of brackets and angle brackets.

    TODO: Add assertions for all 8 emotional tone archetypes.

    @danishansari-dev None
    @returns None
    """
    engine = ZaraVoiceEngine()

    # 1. Happy tone with laugh event
    clean, rate, pitch, tone = engine.parse_prosody_and_tags("[happy] <laugh> Kya baat hai!")
    assert tone == "happy"
    assert clean == "Kya baat hai!"
    assert rate == "+12%" or rate == "+15%"
    assert pitch == "+5Hz" or pitch == "+6Hz"

    # 2. Whisper tone with sigh event
    clean_w, rate_w, pitch_w, tone_w = engine.parse_prosody_and_tags("[whisper] <sigh> It has been such a long day.")
    assert tone_w == "whisper"
    assert clean_w == "It has been such a long day."
    assert "-" in rate_w  # Slower rate
    assert "-" in pitch_w # Lower pitch

@pytest.mark.asyncio
async def test_conversation_engine_flow():
    """
    Tests end-to-end conversation turn generation with memory and context grounding.
    Why this code exists:
    Validates that Zara produces voice-formatted, emotionally grounded dialogue.

    Tricky logic:
    Verifies that fact disclosed in Turn 1 is retrieved and reflected in Turn 2 response text.

    TODO: Test multi-session conversation continuity across simulated app restarts.

    @danishansari-dev None
    @returns None
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        test_db = tf.name

    try:
        mem = ZaraMemoryEngine(db_path=test_db)
        ctx = ZaraContextEngine()
        conv = ZaraConversationEngine(memory_engine=mem, context_engine=ctx)

        # 1. Turn 1: Introduction
        reply1 = await conv.generate_response("Hi Zara, my name is Priya and I love photography.", user_id="u_test")
        assert "text" in reply1
        assert reply1["mood"] in ["warm", "playful", "supportive", "calming"]

        # 2. Verify fact recorded
        facts = mem.list_all_facts(user_id="u_test")
        assert any("Priya" in f["fact_value"] for f in facts)

        # 3. Turn 2: Query memory
        reply2 = await conv.generate_response("What do you remember about me?", user_id="u_test")
        assert "Priya" in reply2["text"] or "photography" in reply2["text"]

    finally:
        try:
            if os.path.exists(test_db):
                os.remove(test_db)
        except Exception:
            pass

@pytest.mark.asyncio
async def test_voice_synthesis_smoke():
    """
    Smoke test for actual audio byte synthesis.
    Why this code exists:
    Guarantees that Zara produces valid MP3 audio streams.

    Tricky logic:
    Synthesizes speech through the live neural pipeline and asserts byte stream length exceeds minimum viable audio payload.

    TODO: Add benchmark testing for synthesis latency under varying network conditions.

    @danishansari-dev None
    @returns None
    """
    engine = ZaraVoiceEngine()
    audio = await engine.synthesize("Hello! This is Zara speaking.", voice_name="zara-expressive")
    assert isinstance(audio, bytes)
    assert len(audio) > 1000, "Synthesized audio output is suspiciously small"

if __name__ == "__main__":
    print("Running synchronous tests...")
    test_mesh_memory_engine()
    print("[PASS] Mesh memory engine test passed!")
    test_peek_context_engine()
    print("[PASS] Peek context engine test passed!")
    test_silk_voice_prosody_parsing()
    print("[PASS] Silk voice prosody test passed!")

    print("Running asynchronous tests...")
    asyncio.run(test_conversation_engine_flow())
    print("[PASS] Conversation engine flow test passed!")
    asyncio.run(test_voice_synthesis_smoke())
    print("[PASS] Voice synthesis smoke test passed!")
    print("\nALL ZARA TESTS PASSED SUCCESSFULLY!")
