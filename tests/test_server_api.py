"""
Server API Integration Tests
Why this file exists:
Verifies HTTP endpoints exposed by Zara FastAPI server (Silk TTS, Chat, Mesh Memory, Peek Context).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from zara.server import app

client = TestClient(app)

def test_voices_endpoint():
    """
    Verifies voice discovery endpoint.
    Why this code exists:
    Confirms client applications can discover available voice personas.

    Tricky logic:
    Asserts presence of standard voice models in the returned catalog dictionary.

    TODO: Add assertions for voice gender and language attributes.

    @danishansari-dev None
    @returns None
    """
    resp = client.get("/v1/voices")
    assert resp.status_code == 200
    data = resp.json()
    assert "voices" in data
    assert "zara-expressive" in data["voices"]
    assert "zara-hinglish" in data["voices"]

def test_tts_json_endpoint():
    """
    Verifies TTS generation in JSON mode.
    Why this code exists:
    Matches Rumik's /v1/tts endpoint with as_json parameter.

    Tricky logic:
    Asserts that base64 encoded audio string is returned with valid length.

    TODO: Add base64 decoding check to ensure non-empty byte buffer.

    @danishansari-dev None
    @returns None
    """
    resp = client.post("/v1/tts", json={
        "text": "[happy] Hello world!",
        "voice": "zara-expressive",
        "as_json": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "audio_base64" in data
    assert len(data["audio_base64"]) > 50

def test_chat_and_memory_cycle():
    """
    Verifies conversational chat and memory persistence through API.
    Why this code exists:
    Tests end-to-end integration across conversation, memory, context, and voice.

    Tricky logic:
    Performs full lifecycle: clear memory -> send disclosure message -> inspect retrieved facts -> delete fact -> verify count decrement.

    TODO: Test concurrent requests from multiple distinct users simultaneously.

    @danishansari-dev None
    @returns None
    """
    # 1. Clear test user memories first
    client.post("/v1/memory/clear?user_id=api_test_user")

    # 2. Chat with disclosure
    chat_resp = client.post("/v1/agents/chat", json={
        "message": "Hi Zara! My name is Aanya and I live in Pune.",
        "voice": "zara-hinglish",
        "user_id": "api_test_user"
    })
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "reply" in chat_data
    assert "audio_base64" in chat_data
    assert "subtext" in chat_data

    # 3. Check memory endpoint
    mem_resp = client.get("/v1/memory?user_id=api_test_user")
    assert mem_resp.status_code == 200
    mem_data = mem_resp.json()
    assert mem_data["count"] >= 2
    facts = mem_data["facts"]
    assert any("Aanya" in f["fact_value"] for f in facts)
    assert any("Pune" in f["fact_value"] for f in facts)

    # 4. Delete one fact
    first_id = facts[0]["id"]
    del_resp = client.delete(f"/v1/memory/{first_id}?user_id=api_test_user")
    assert del_resp.status_code == 200

    # 5. Verify deletion
    mem_resp_after = client.get("/v1/memory?user_id=api_test_user")
    assert mem_resp_after.json()["count"] == mem_data["count"] - 1

def test_context_analyze_endpoint():
    """
    Verifies Peek context diagnostics endpoint.
    Why this code exists:
    Tests API-level subtext and Hinglish cultural detection.

    Tricky logic:
    Passes Hinglish phrase and asserts subtext, temporal, and Hinglish token detections.

    TODO: Add benchmark on response latency for the context analyzer endpoint.

    @danishansari-dev None
    @returns None
    """
    resp = client.post("/v1/context/analyze", json={
        "text": "Arre yaar, I am fine."
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "temporal" in data
    assert "hinglish" in data
    assert data["hinglish"]["is_hinglish"] is True
    assert "subtext" in data

if __name__ == "__main__":
    print("Running API tests...")
    test_voices_endpoint()
    print("[PASS] Voices endpoint passed!")
    test_tts_json_endpoint()
    print("[PASS] TTS JSON endpoint passed!")
    test_chat_and_memory_cycle()
    print("[PASS] Chat and memory cycle passed!")
    test_context_analyze_endpoint()
    print("[PASS] Context analyze endpoint passed!")
    print("\nALL SERVER API TESTS PASSED SUCCESSFULLY!")
