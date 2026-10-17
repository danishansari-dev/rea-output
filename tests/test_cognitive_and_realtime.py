"""
Cognitive Memory, Context Intelligence & Real-Time Gateway Test Suite
Why this file exists:
Verifies advanced cognitive memory extractions (compound location transitions, age, birthday,
pets, preference negations), expanded Hinglish idiom recognition, conversational intent
classification, health/stats endpoints, and WebSocket real-time interruption handling.
"""

import os
import sys
import json
import pytest
from fastapi.testclient import TestClient

# Ensure root directory is on pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from zara.server import app
from zara.memory_engine import ZaraMemoryEngine
from zara.context_engine import ZaraContextEngine

client = TestClient(app)

def test_compound_location_transition():
    """
    Verifies that compound statements like 'I used to live in X but now live in Y'
    correctly record the present city Y rather than the historical city X.
    Why this code exists:
    Prevents historical context from overriding the user's active geographic presence.

    Tricky logic:
    Evaluates presence of 'used to live' vs 'now live in' / 'moved to' patterns to assign current_city.

    TODO: Support tracking previous_city as a secondary historical slot.

    @danishansari-dev None
    @returns None
    """
    engine = ZaraMemoryEngine(db_path=":memory:")
    engine.record_user_turn("I used to live in Mumbai, but now I live in London.", user_id="u_transition")
    facts = engine.list_all_facts(user_id="u_transition")
    loc_facts = [f for f in facts if f["key_slot"] == "current_city"]

    assert len(loc_facts) == 1, f"Expected exactly 1 location fact, got: {loc_facts}"
    assert "London" in loc_facts[0]["fact_value"], f"Expected London, got: {loc_facts[0]['fact_value']}"
    assert "Mumbai" not in loc_facts[0]["fact_value"]

def test_age_and_birthday_extraction():
    """
    Verifies extraction of user age and birthday disclosures.
    Why this code exists:
    Grounds companion birthday wishes and age-appropriate conversational tone.

    Tricky logic:
    Parses numeric age patterns and month/day string sequences into structured slots.

    TODO: Calculate real-time age dynamically if year of birth is supplied.

    @danishansari-dev None
    @returns None
    """
    engine = ZaraMemoryEngine(db_path=":memory:")
    engine.record_user_turn("I am 27 years old and my birthday is in August.", user_id="u_bio")
    facts = engine.list_all_facts(user_id="u_bio")

    age_fact = next((f for f in facts if f["key_slot"] == "user_age"), None)
    bday_fact = next((f for f in facts if f["key_slot"] == "birthday"), None)

    assert age_fact is not None, "Age fact was not extracted"
    assert "27" in age_fact["fact_value"]
    assert bday_fact is not None, "Birthday fact was not extracted"
    assert "August" in bday_fact["fact_value"]

def test_pet_relationship_extraction():
    """
    Verifies extraction of domestic pet disclosures.
    Why this code exists:
    Pets are central emotional companions for users; remembering pet names is a core Rumik/Ira trait.

    Tricky logic:
    Matches animal species keywords (dog, cat, puppy, kitten) and captures name or breed.

    TODO: Support multi-pet tracking under indexed slots (pet_1, pet_2).

    @danishansari-dev None
    @returns None
    """
    engine = ZaraMemoryEngine(db_path=":memory:")
    engine.record_user_turn("My dog's name is Bruno and my cat is Luna.", user_id="u_pets")
    facts = engine.list_all_facts(user_id="u_pets")

    dog_fact = next((f for f in facts if "dog" in f["key_slot"]), None)
    cat_fact = next((f for f in facts if "cat" in f["key_slot"]), None)

    assert dog_fact is not None, "Dog fact was not extracted"
    assert "Bruno" in dog_fact["fact_value"]
    assert cat_fact is not None, "Cat fact was not extracted"
    assert "Luna" in cat_fact["fact_value"]

def test_preference_negation_and_dislikes():
    """
    Verifies extraction of expressed dislikes and food/hobby aversions.
    Why this code exists:
    Prevents the companion from recommending things the user actively dislikes or avoids.

    Tricky logic:
    Distinguishes positive 'i like' from negative 'i don't like' or 'i hate'.

    TODO: Add allergy severity level classification (mild aversion vs medical allergy).

    @danishansari-dev None
    @returns None
    """
    engine = ZaraMemoryEngine(db_path=":memory:")
    engine.record_user_turn("I really hate spicy food and I don't like coffee.", user_id="u_dislikes")
    facts = engine.list_all_facts(user_id="u_dislikes")

    dislike_facts = [f for f in facts if f["category"] == "dislike"]
    assert len(dislike_facts) >= 1, f"Expected at least 1 dislike fact, got: {facts}"
    assert any("spicy" in f["fact_value"].lower() or "coffee" in f["fact_value"].lower() for f in dislike_facts)

def test_expanded_hinglish_idioms():
    """
    Verifies detection of everyday colloquial Hindi-English idioms expressing fatigue and relief.
    Why this code exists:
    Validates Peek's cultural intelligence across common bilingual expressions.

    Tricky logic:
    Inspects expressions like 'bohot thak gaya' and 'scene sorted hai' to map to nuanced subtext.

    TODO: Expand Devanagari transliteration matching for non-standard phonetic spellings.

    @danishansari-dev None
    @returns None
    """
    engine = ZaraContextEngine()

    # 1. Fatigue idiom: 'bohot thak gaya hoon'
    res_fatigue = engine.decode_emotional_subtext("Bohot thak gaya hoon aaj yaar.", {"period": "evening"}, [])
    assert res_fatigue["subtext_detected"] is True
    assert res_fatigue["underlying_emotion"] == "emotional_fatigue"

    # 2. Exasperation idiom: 'dimag ka dahi'
    res_exasperated = engine.decode_emotional_subtext("Poora din kaam kiya, dimag ka dahi ho gaya.", {"period": "evening"}, [])
    assert res_exasperated["subtext_detected"] is True
    assert res_exasperated["underlying_emotion"] in ["burnout_overwhelm", "emotional_fatigue"]

    # 3. Sorted idiom: 'scene sorted hai'
    res_sorted = engine.decode_emotional_subtext("Finally sab kaam khatam, scene sorted hai!", {"period": "evening"}, [])
    assert res_sorted["subtext_detected"] is True
    assert res_sorted["underlying_emotion"] == "celebratory_excitement"

def test_conversational_intent_classification():
    """
    Verifies that user utterances are classified into actionable intent categories.
    Why this code exists:
    Enables conversational responses to adapt their depth, pacing, and tone to the user's intent.

    Tricky logic:
    Differentiates advice-seeking questions from venting statements and memory inquiries.

    TODO: Train multi-label intent classifier for compound dialogue turns.

    @danishansari-dev None
    @returns None
    """
    engine = ZaraContextEngine()

    # 1. Advice intent
    intent_advice = engine.classify_conversational_intent("Zara, can you give me some advice on handling workplace burnout?")
    assert intent_advice["primary_intent"] == "seeking_advice"

    # 2. Memory inquiry intent
    intent_memory = engine.classify_conversational_intent("What do you remember about my career and where I live?")
    assert intent_memory["primary_intent"] == "memory_inquiry"

    # 3. Venting intent
    intent_vent = engine.classify_conversational_intent("I just need to vent... today was a complete disaster.")
    assert intent_vent["primary_intent"] == "venting"

def test_health_and_stats_endpoints():
    """
    Verifies the server health probe and statistics diagnostic endpoints.
    Why this code exists:
    Essential for production observability, container orchestration, and runtime telemetry.

    Tricky logic:
    Asserts HTTP 200 and schema compliance on both /v1/health and /v1/stats.

    TODO: Add database connection pool latency metric to stats response.

    @danishansari-dev None
    @returns None
    """
    # 1. Health endpoint
    resp_health = client.get("/v1/health")
    assert resp_health.status_code == 200
    health_data = resp_health.json()
    assert health_data["status"] == "healthy"
    assert "version" in health_data

    # 2. Stats endpoint
    resp_stats = client.get("/v1/stats")
    assert resp_stats.status_code == 200
    stats_data = resp_stats.json()
    assert "total_facts" in stats_data
    assert "supported_voices" in stats_data
    assert stats_data["supported_voices"] >= 6

def test_websocket_interruption_event():
    """
    Verifies that the WebSocket gateway accepts 'interrupt' action events and emits an acknowledgment.
    Why this code exists:
    Provides immediate barge-in capability when the user begins speaking while audio is playing.

    Tricky logic:
    Sends an interrupt action frame and asserts the server acknowledges with an 'interrupted' event.

    TODO: Track millisecond latency between interrupt frame and client audio cessation.

    @danishansari-dev None
    @returns None
    """
    with client.websocket_connect("/v1/realtime") as ws:
        # Send interrupt command
        ws.send_text(json.dumps({"action": "interrupt"}))
        msg = ws.receive_text()
        data = json.loads(msg)
        assert data["event"] == "interrupted"
        assert data["status"] == "stream_halted"

if __name__ == "__main__":
    print("Running Cognitive & Real-Time Gateway Test Suite...")
    test_compound_location_transition()
    print("[PASS] Compound location transition passed!")
    test_age_and_birthday_extraction()
    print("[PASS] Age & birthday extraction passed!")
    test_pet_relationship_extraction()
    print("[PASS] Pet relationship extraction passed!")
    test_preference_negation_and_dislikes()
    print("[PASS] Preference negation & dislikes passed!")
    test_expanded_hinglish_idioms()
    print("[PASS] Expanded Hinglish idioms passed!")
    test_conversational_intent_classification()
    print("[PASS] Conversational intent classification passed!")
    test_health_and_stats_endpoints()
    print("[PASS] Health and stats endpoints passed!")
    test_websocket_interruption_event()
    print("[PASS] WebSocket interruption event passed!")
    print("\nALL COGNITIVE & REAL-TIME TESTS PASSED!")
