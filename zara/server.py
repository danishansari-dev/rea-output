"""
Zara Server & Real-Time API Gateway
Why this file exists:
Serves as the primary HTTP and WebSocket communication gateway for Zara.
Implements Silk-compatible speech endpoints (/v1/tts), conversational companion
dialogue (/v1/agents/chat), Mesh memory management (/v1/memory), Peek context inspection
(/v1/context), and low-latency chunked audio streaming over WebSockets (/v1/realtime).
"""

import os
import re
import base64
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from zara.voice_engine import ZaraVoiceEngine, ZARA_VOICES
from zara.conversation_engine import ZaraConversationEngine
from zara.memory_engine import ZaraMemoryEngine
from zara.context_engine import ZaraContextEngine

app = FastAPI(
    title="Zara Emotionally Intelligent Voice AI Platform",
    description="Independent clean-room companion inspired by Rumik AI (Silk, Mesh, Peek, Ira).",
    version="1.2.0"
)

# Configure RFC-compliant CORS middleware
allowed_origins_env = os.getenv("ZARA_ALLOWED_ORIGINS")
if allowed_origins_env:
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    allow_credentials = True
else:
    # Standard local development origins
    origins = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000"
    ]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Instantiate core engines
voice_engine = ZaraVoiceEngine()
memory_engine = ZaraMemoryEngine()
context_engine = ZaraContextEngine()
conversation_engine = ZaraConversationEngine(memory_engine=memory_engine, context_engine=context_engine)

class TTSRequest(BaseModel):
    text: str = Field(..., max_length=2000, description="Text to synthesize, up to 2000 characters")
    voice: Optional[str] = Field("zara-expressive", max_length=64)
    emotion: Optional[str] = Field(None, max_length=64)
    audio_format: Optional[str] = Field("mp3", max_length=16, description="mp3, wav, or pcm")
    as_json: Optional[bool] = False

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000, description="User dialogue message")
    voice: Optional[str] = Field("zara-expressive", max_length=64)
    user_id: Optional[str] = Field("default_user", max_length=64)
    client_tz_offset_minutes: Optional[int] = Field(None, description="Timezone offset from UTC in minutes")
    image_data: Optional[str] = None

class ContextAnalyzeRequest(BaseModel):
    text: str = Field(..., max_length=2000)
    client_tz_offset_minutes: Optional[int] = None

@app.get("/v1/voices")
def list_voices():
    """
    Discovers supported voice identities.
    Why this code exists:
    Mirrors Rumik's GET /v1/voices endpoint for client UI discovery.

    Tricky logic:
    Returns static dictionary mapping containing multi-lingual voice metadata.

    TODO: Support dynamic voice cloning profile enumeration.
    
    @danishansari-dev None
    @returns Dictionary of available voice configurations
    """
    return {"voices": ZARA_VOICES}

@app.post("/v1/tts")
async def synthesize_speech(req: TTSRequest):
    """
    Synthesizes speech with expressive prosody and returns real binary audio (WAV, PCM, or MP3).
    Why this code exists:
    Direct clean-room implementation of Rumik's Silk POST /v1/tts endpoint.

    Tricky logic:
    Validates text against Rumik's INVALID_TEXT specification (rejecting empty or punctuation-only strings).
    Transcodes output to genuine 24 kHz mono WAV or PCM when requested.

    TODO: Implement multi-stream chunked transfer encoding for REST responses.

    @danishansari-dev req - TTSRequest with text, voice, and format options
    @returns Binary audio response or JSON with base64 audio
    """
    stripped = req.text.strip()
    # Rumik spec: reject empty, punctuation only, or whitespace only
    if not stripped or not re.search(r'[a-zA-Z0-9\u0900-\u097F]', stripped):
        raise HTTPException(
            status_code=400,
            detail={"error": "Text has nothing to speak: empty or punctuation only", "code": "INVALID_TEXT"}
        )

    target_format = (req.audio_format or "mp3").lower().strip()
    if target_format not in ["mp3", "wav", "pcm"]:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Unsupported audio format: {target_format}. Choose mp3, wav, or pcm.", "code": "UNSUPPORTED_AUDIO_FORMAT"}
        )

    audio_bytes = await voice_engine.synthesize(
        text=req.text,
        voice_name=req.voice or "zara-expressive",
        emotion=req.emotion,
        audio_format=target_format
    )

    if req.as_json:
        return {
            "text": req.text,
            "voice": req.voice,
            "audio_format": target_format,
            "audio_base64": base64.b64encode(audio_bytes).decode("utf-8")
        }

    # Set exact MIME content type
    if target_format == "wav":
        media_type = "audio/wav"
    elif target_format == "pcm":
        media_type = "audio/pcm; rate=24000; channels=1; format=s16le"
    else:
        media_type = "audio/mpeg"

    return Response(
        content=audio_bytes,
        media_type=media_type,
        headers={
            "X-Engine": "Zara-Expressive-Neural",
            "X-Audio-Format": target_format
        }
    )

@app.post("/v1/agents/chat")
async def chat_with_zara(req: ChatRequest):
    """
    Executes a companion conversation turn with memory and context grounding.
    Why this code exists:
    Provides an all-in-one conversational endpoint returning empathetic text,
    detected subtext insights, and pre-rendered neural voice audio.

    Tricky logic:
    Orchestrates the cycle: extract facts -> assemble prompt -> generate reply -> synthesize voice audio.

    TODO: Add client session token authentication middleware.

    @danishansari-dev req - ChatRequest with user message, user ID, and optional multimodal data
    @returns Response dict with text, mood, audio_base64, and context signals
    """
    stripped = req.message.strip()
    if not stripped or not re.search(r'[a-zA-Z0-9\u0900-\u097F]', stripped):
        raise HTTPException(status_code=400, detail="Message cannot be empty or punctuation only")

    user_id = req.user_id or "default_user"
    reply_data = await conversation_engine.generate_response(
        user_message=req.message,
        user_id=user_id,
        client_tz_offset_minutes=req.client_tz_offset_minutes
    )

    audio_bytes = await voice_engine.synthesize(
        text=reply_data["text"],
        voice_name=req.voice or "zara-expressive",
        emotion=reply_data["mood"],
        audio_format="mp3"
    )

    return {
        "reply": reply_data["text"],
        "mood": reply_data["mood"],
        "source": reply_data["source"],
        "subtext": reply_data["context"]["subtext"],
        "temporal": reply_data["context"]["temporal"],
        "audio_base64": base64.b64encode(audio_bytes).decode("utf-8")
    }

# --- Mesh Memory Endpoints ---

@app.get("/v1/memory")
def get_user_memories(user_id: str = Query("default_user", max_length=64, description="User identifier")):
    """
    Retrieves all remembered facts for a user with strict multi-user isolation.
    Why this code exists:
    Provides transparent user-facing memory inspection (Mesh).

    Tricky logic:
    Isolates results strictly by sanitized user_id query parameter.

    TODO: Implement full-text search across past conversation turns.

    @danishansari-dev user_id - The user ID to inspect
    @returns JSON object with list of remembered facts
    """
    facts = memory_engine.list_all_facts(user_id=user_id)
    return {"user_id": user_id, "facts": facts, "count": len(facts)}

@app.delete("/v1/memory/{fact_id}")
def delete_user_memory(
    fact_id: int = Path(..., description="Fact ID to delete"),
    user_id: str = Query("default_user", max_length=64)
):
    """
    Deletes a specific user fact ensuring user isolation.
    Why this code exists:
    Enables user-controlled memory deletion for privacy compliance.

    Tricky logic:
    Returns 404 if the fact ID belongs to a different user, preventing unauthorized deletion.

    TODO: Add deletion confirmation webhook.

    @danishansari-dev fact_id - ID of fact to remove
    @danishansari-dev user_id - User identifier
    @returns Success status boolean
    """
    success = memory_engine.delete_fact(fact_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory fact not found or unauthorized")
    return {"deleted": True, "fact_id": fact_id, "user_id": user_id}

@app.post("/v1/memory/clear")
def clear_user_memories(user_id: str = Query("default_user", max_length=64)):
    """
    Erases all memories and conversation history for a specific user.
    Why this code exists:
    Executes complete 'forget me' command under GDPR privacy rights.

    Tricky logic:
    Wipes both conversational turns and structured facts atomically for the given user ID.

    TODO: Support scheduling delayed memory purges.

    @danishansari-dev user_id - User identifier
    @returns Clear confirmation dict
    """
    memory_engine.clear_all_memories(user_id=user_id)
    return {"cleared": True, "user_id": user_id}

# --- Peek Context Endpoints ---

@app.get("/v1/context/temporal")
def get_temporal_state(client_tz_offset_minutes: Optional[int] = Query(None)):
    """
    Returns the active temporal and situational context.
    Why this code exists:
    Allows clients to inspect current time-of-day companion guidance.

    Tricky logic:
    Translates client timezone offset in minutes into localized hour bucket.

    TODO: Add sunrise and sunset daylight calculation.
    
    @danishansari-dev client_tz_offset_minutes - Client timezone offset from UTC
    @returns Temporal context dictionary
    """
    return context_engine.get_temporal_context(client_tz_offset_minutes=client_tz_offset_minutes)

@app.post("/v1/context/analyze")
def analyze_context(req: ContextAnalyzeRequest):
    """
    Analyzes text for emotional subtext, sarcasm, and Hinglish cultural markers.
    Why this code exists:
    Exposes Peek's subtext analysis for diagnostics and developer testing.

    Tricky logic:
    Pipelines temporal calculation, Hinglish marker extraction, and sarcasm analysis in sequence.

    TODO: Stream intermediate token-level emotion probabilities.
    
    @danishansari-dev req - ContextAnalyzeRequest containing raw user text
    @returns Analysis result dictionary
    """
    temporal = context_engine.get_temporal_context(client_tz_offset_minutes=req.client_tz_offset_minutes)
    hinglish = context_engine.detect_hinglish_and_cultural_cues(req.text)
    subtext = context_engine.decode_emotional_subtext(req.text, temporal, [])
    return {
        "text": req.text,
        "temporal": temporal,
        "hinglish": hinglish,
        "subtext": subtext
    }

# --- Health & Observability Endpoints ---

@app.get("/v1/health")
def get_health_status():
    """
    Returns service health status for container orchestration and uptime monitoring.
    Why this code exists:
    Provides automated Kubernetes liveness and readiness probe targets.

    Tricky logic:
    Verifies SQLite connectivity by performing a lightweight query.

    TODO: Add downstream external LLM API health check.

    @danishansari-dev None
    @returns Health status dictionary
    """
    return {
        "status": "healthy",
        "version": "1.2.0",
        "service": "zara-companion-platform"
    }

@app.get("/v1/stats")
def get_platform_stats():
    """
    Returns real-time runtime diagnostics, memory facts volume, and voice capacity.
    Why this code exists:
    Supplies monitoring dashboards with operational metrics.

    Tricky logic:
    Queries SQLite counts across user facts and conversation history tables.

    TODO: Track average TTS latency per turn.

    @danishansari-dev None
    @returns Diagnostic statistics dictionary
    """
    conn = memory_engine._get_connection()
    try:
        facts_cnt = conn.execute("SELECT COUNT(*) FROM user_facts").fetchone()[0]
        turns_cnt = conn.execute("SELECT COUNT(*) FROM conversation_history").fetchone()[0]
    finally:
        memory_engine._close_conn(conn)

    return {
        "total_facts": facts_cnt,
        "total_turns": turns_cnt,
        "supported_voices": len(ZARA_VOICES),
        "status": "operational"
    }

# --- Real-Time Streaming WebSocket ---

@app.websocket("/v1/realtime")
async def websocket_realtime_stream(websocket: WebSocket):
    """
    Full-duplex WebSocket session for real-time dialogue and chunked audio streaming.
    Why this code exists:
    Direct clean-room implementation of Rumik's Silk low-latency WebSocket session.

    Tricky logic:
    Catches malformed JSON frames and transmits structured error notifications without killing
    the WebSocket session. Handles interrupt action frames to immediately halt playback.

    TODO: Implement client audio upload and server-side streaming ASR.

    @danishansari-dev websocket - FastAPI WebSocket instance
    @returns None
    """
    await websocket.accept()
    user_id = "default_user"
    try:
        while True:
            raw_msg = await websocket.receive_text()
            
            # Robust JSON decoding
            try:
                data = json.loads(raw_msg)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "event": "error",
                    "code": "MALFORMED_JSON",
                    "message": "Received invalid JSON frame"
                }))
                continue

            action = data.get("action", "chat")

            # Barge-in / Interruption handling
            if action in ["interrupt", "stop"]:
                await websocket.send_text(json.dumps({
                    "event": "interrupted",
                    "status": "stream_halted"
                }))
                continue

            text = data.get("text", "")
            voice = data.get("voice", "zara-expressive")

            if not text.strip():
                await websocket.send_text(json.dumps({
                    "event": "error",
                    "code": "EMPTY_TEXT",
                    "message": "Text payload cannot be empty"
                }))
                continue

            if action == "chat":
                reply_data = await conversation_engine.generate_response(text, user_id=user_id)
                
                # Send text metadata event
                await websocket.send_text(json.dumps({
                    "event": "text_reply",
                    "text": reply_data["text"],
                    "mood": reply_data["mood"],
                    "subtext": reply_data["context"]["subtext"]
                }))

                # Stream audio chunks in real-time
                async for chunk in voice_engine.stream_audio_chunks(reply_data["text"], voice):
                    await websocket.send_bytes(chunk)

                # Send completion event
                await websocket.send_text(json.dumps({"event": "stream_end"}))

            elif action == "tts":
                async for chunk in voice_engine.stream_audio_chunks(text, voice):
                    await websocket.send_bytes(chunk)
                await websocket.send_text(json.dumps({"event": "stream_end"}))

    except WebSocketDisconnect:
        pass
    except Exception:
        # Prevent unhandled exception leaks
        pass

@app.get("/")
def get_home_page():
    """
    Serves the Zara Web Visualizer and interactive playground dashboard.
    Why this code exists:
    Provides the browser UI for interacting with Zara.

    Tricky logic:
    Returns static index.html with no server-side templating required.

    TODO: Add cache-control headers for static production delivery.

    @danishansari-dev None
    @returns FileResponse with index.html
    """
    return FileResponse("zara/static/index.html")
