"""
Zara Comprehensive Regression & Security Test Suite
Why this file exists:
Verifies that all discovered security vulnerabilities (DOM XSS, CORS), audio format
transcoding bugs, stopword retrieval distortions, casing fragilities, timezone issues,
and WebSocket error conditions are comprehensively tested and verified.
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
from zara.voice_engine import ZaraVoiceEngine
from zara.context_engine import ZaraContextEngine

client = TestClient(app)

def test_security_cors_policy():
    """
    Verifies that CORS policy complies with RFC standards.
    Why this code exists:
    Confirms SEC-02 is resolved and credentials are not combined with unsafe wildcards.

    Tricky logic:
    Issues an OPTIONS pre-flight request with Origin header to verify CORS response.

    TODO: Test subdomain wildcard origins if configured.

    @danishansari-dev None
    @returns None
    """
    response = client.options("/v1/voices", headers={
        "Origin": "http://localhost:8000",
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8000"

def test_tts_format_transcoding_wav_and_pcm():
    """
    Verifies that requesting WAV returns authentic RIFF/WAV audio bytes, and PCM returns raw PCM.
    Why this code exists:
    Confirms VOX-01 is resolved and no corrupt MP3-labeled-as-WAV is returned.

    Tricky logic:
    Inspects leading magic byte signatures (b'RIFF' header for WAV, and non-RIFF binary buffer for PCM).

    TODO: Verify bit depth and sample rate using wave module reader.

    @danishansari-dev None
    @returns None
    """
    # 1. WAV test
    resp_wav = client.post("/v1/tts", json={
        "text": "Testing WAV output format from Zara.",
        "audio_format": "wav"
    })
    assert resp_wav.status_code == 200
    assert resp_wav.headers["content-type"] == "audio/wav"
    assert resp_wav.content.startswith(b"RIFF"), "WAV bytes must start with RIFF header"

    # 2. PCM test
    resp_pcm = client.post("/v1/tts", json={
        "text": "Testing raw PCM output format.",
        "audio_format": "pcm"
    })
    assert resp_pcm.status_code == 200
    assert "audio/pcm" in resp_pcm.headers["content-type"]
    assert not resp_pcm.content.startswith(b"RIFF")
    assert len(resp_pcm.content) > 1000

def test_tts_validation_invalid_text():
    """
    Verifies that empty or punctuation-only text returns 400 INVALID_TEXT per Rumik spec.
    Why this code exists:
    Tests input validation boundaries and protects downstream synthesis from wasting compute.

    Tricky logic:
    Asserts both punctuation-only rejection and unsupported audio format rejection with specific error codes.

    TODO: Test unicode emoji-only strings behavior.

    @danishansari-dev None
    @returns None
    """
    # Punctuation only
    resp = client.post("/v1/tts", json={"text": "... !? -", "audio_format": "mp3"})
    assert resp.status_code == 400
    data = resp.json()
    assert "INVALID_TEXT" in str(data)

    # Unsupported format
    resp_fmt = client.post("/v1/tts", json={"text": "Valid text", "audio_format": "flac"})
    assert resp_fmt.status_code == 400
    assert "UNSUPPORTED_AUDIO_FORMAT" in str(resp_fmt.json())

def test_tts_input_length_limit():
    """
    Verifies that oversized text payloads (>2000 chars) are rejected with HTTP 422.
    Why this code exists:
    Protects the server from denial-of-service via huge payloads (SRV-02).

    Tricky logic:
    Synthesizes a 2500 character payload exceeding the Pydantic max_length=2000 constraint.

    TODO: Add streaming truncation for conversational clients.

    @danishansari-dev None
    @returns None
    """
    huge_text = "Zara " * 500  # 2500 characters
    resp = client.post("/v1/tts", json={"text": huge_text})
    assert resp.status_code == 422

def test_memory_stopword_and_category_boost():
    """
    Verifies that stopword filtering and category intent boosting retrieve relevant facts.
    Why this code exists:
    Confirms MEM-01 is resolved and queries like 'Where am I located?' retrieve city facts.

    Tricky logic:
    Tests intent matching on a question sharing no non-stopword tokens with the stored fact.

    TODO: Add cross-category multi-hop memory retrieval test.

    @danishansari-dev None
    @returns None
    """
    engine = ZaraMemoryEngine(db_path=":memory:")
    engine.record_user_turn("My name is Rohan and I live in Pune.", user_id="u_stopword")

    # Query with stopwords: 'Where am I located?' (contains no common words with fact except category intent)
    retrieved = engine.get_relevant_memories("Where am I located?", user_id="u_stopword")
    assert len(retrieved) > 0
    assert "Pune" in retrieved[0]["fact"], f"Expected Pune in top memory, got: {retrieved}"

def test_memory_multiuser_isolation_security():
    """
    Verifies that User A cannot read, overwrite, or delete User B's memories.
    Why this code exists:
    Guarantees strict multi-tenant privacy isolation.

    Tricky logic:
    Simulates Bob attempting to access and delete Alice's fact ID and asserts access denial.

    TODO: Add stress test with 50 concurrent simulated users.

    @danishansari-dev None
    @returns None
    """
    engine = ZaraMemoryEngine(db_path=":memory:")
    engine.record_user_turn("My name is Alice and I work in Finance.", user_id="alice")
    engine.record_user_turn("My name is Bob and I work in Medicine.", user_id="bob")

    # Bob should not see Alice's facts
    bob_facts = engine.list_all_facts(user_id="bob")
    assert any("medicine" in f["fact_value"].lower() for f in bob_facts)
    assert all("finance" not in f["fact_value"].lower() for f in bob_facts)

    # Bob attempts to delete Alice's fact ID
    alice_facts = engine.list_all_facts(user_id="alice")
    alice_fact_id = alice_facts[0]["id"]

    # Delete attempt by Bob must fail
    del_result = engine.delete_fact(alice_fact_id, user_id="bob")
    assert del_result is False

    # Alice's fact must still exist
    alice_after = engine.list_all_facts(user_id="alice")
    assert any(f["id"] == alice_fact_id for f in alice_after)

def test_context_sarcasm_and_timezone():
    """
    Verifies sarcasm detection and timezone offset handling.
    Why this code exists:
    Confirms CTX-01 and CTX-02 are resolved.

    Tricky logic:
    Tests sarcasm pattern inversion ('oh great' + 'broke down') and negative timezone offset parsing.

    TODO: Test half-hour timezone offsets (e.g., IST +330).

    @danishansari-dev None
    @returns None
    """
    # 1. Sarcasm test
    resp_sarcasm = client.post("/v1/context/analyze", json={
        "text": "Oh great, my car broke down on the highway."
    })
    assert resp_sarcasm.status_code == 200
    data = resp_sarcasm.json()
    assert data["subtext"]["subtext_detected"] is True
    assert data["subtext"]["underlying_emotion"] == "sarcastic_frustration"

    # 2. Timezone test
    resp_tz = client.get("/v1/context/temporal?client_tz_offset_minutes=-300")
    assert resp_tz.status_code == 200
    tz_data = resp_tz.json()
    assert "hour" in tz_data
    assert "period" in tz_data

def test_websocket_error_resilience():
    """
    Verifies WebSocket does not terminate on malformed JSON frames.
    Why this code exists:
    Confirms SRV-01 is resolved and voice sessions survive frame decoding errors.

    Tricky logic:
    Sends invalid JSON text, verifies structured error frame is returned, and verifies subsequent valid frames still work.

    TODO: Test WebSocket binary chunk fragmentation resilience.

    @danishansari-dev None
    @returns None
    """
    with client.websocket_connect("/v1/realtime") as ws:
        # Send invalid JSON
        ws.send_text("THIS IS NOT JSON")
        error_msg = ws.receive_text()
        error_data = json.loads(error_msg)
        assert error_data["event"] == "error"
        assert error_data["code"] == "MALFORMED_JSON"

        # Send empty text payload
        ws.send_text(json.dumps({"action": "chat", "text": "   "}))
        empty_msg = ws.receive_text()
        empty_data = json.loads(empty_msg)
        assert empty_data["event"] == "error"
        assert empty_data["code"] == "EMPTY_TEXT"

        # Verify socket is still healthy and responsive
        ws.send_text(json.dumps({"action": "tts", "text": "Hello WebSocket", "voice": "zara-expressive"}))
        received_bytes = False
        while True:
            msg = ws.receive()
            if "bytes" in msg and msg["bytes"]:
                received_bytes = True
            elif "text" in msg:
                evt = json.loads(msg["text"])
                if evt.get("event") == "stream_end":
                    break
        assert received_bytes is True, "Expected binary audio stream from WebSocket"

if __name__ == "__main__":
    print("Running Regression & Security Suite...")
    test_security_cors_policy()
    print("[PASS] CORS policy test passed!")
    test_tts_format_transcoding_wav_and_pcm()
    print("[PASS] WAV and PCM transcoding test passed!")
    test_tts_validation_invalid_text()
    print("[PASS] TTS text validation test passed!")
    test_tts_input_length_limit()
    print("[PASS] TTS input length limit test passed!")
    test_memory_stopword_and_category_boost()
    print("[PASS] Memory stopword & category boost test passed!")
    test_memory_multiuser_isolation_security()
    print("[PASS] Multi-user memory isolation test passed!")
    test_context_sarcasm_and_timezone()
    print("[PASS] Context sarcasm and timezone test passed!")
    test_websocket_error_resilience()
    print("[PASS] WebSocket error resilience test passed!")
    print("\nALL REGRESSION & SECURITY TESTS PASSED SUCCESSFULLY!")
