"""
Zara Voice Model Training & Dataset Pipeline Test Suite
Why this file exists:
Verifies the end-to-end functionality of the dataset preparation engine,
manifest generator, Mulberry voice description resolver, PyTorch training engine,
and objective acoustic evaluation metrics.
"""

import os
import io
import json
import wave
import struct
import math
import shutil
import tempfile
import pytest

from training.voice.prepare_dataset import (
    inspect_audio_file,
    parse_transcript_metadata,
    process_single_audio,
    prepare_voice_dataset
)
from training.voice.train_voice import (
    VoiceManifestDataset,
    LightweightSpeechLM,
    run_voice_training,
    detect_hardware
)
from training.voice.evaluate_voice import (
    analyze_pcm_audio,
    verify_tag_adherence
)
from zara.voice_engine import ZaraVoiceEngine


def create_synthetic_wav(filepath: str, duration_sec: float = 2.0, sample_rate: int = 24000):
    """
    Helper function to generate a clean synthetic 24 kHz 16-bit mono sine wave WAV file
    Why this code exists:
    Provides deterministic, zero-dependency audio files for unit testing the dataset pipeline.

    Tricky logic:
    Generates a 440 Hz standard concert pitch A sine tone using struct pack.

    @danishansari-dev filepath - Destination path for WAV file
    @danishansari-dev duration_sec - Duration in seconds
    @danishansari-dev sample_rate - Sampling rate (24000 Hz)
    @returns None
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    n_samples = int(duration_sec * sample_rate)
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            # 440 Hz sine tone with amplitude 16000 (approx -6 dBFS)
            val = int(16000.0 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
            frames.extend(struct.pack('<h', val))
        wf.writeframes(frames)


def test_transcript_metadata_parser():
    """
    Verifies that emotional tone tags and inline paralinguistics are parsed accurately.
    Why this code exists:
    Ensures that manifest metadata indexes tone and inline events without corrupting speech text.

    Tricky logic:
    Tests multiple bracket formats and XML-style inline tags.

    TODO: Test nested and multi-tag utterances.

    @danishansari-dev None
    @returns None
    """
    res1 = parse_transcript_metadata("[happy] Arre wah! I knew you could do it! <laugh>")
    assert res1["detected_tone"] == "happy"
    assert "laugh" in res1["inline_events"]
    assert res1["clean_text"] == "Arre wah! I knew you could do it!"

    res2 = parse_transcript_metadata("[whisper] It's really late now... <sigh>")
    assert res2["detected_tone"] == "whisper"
    assert "sigh" in res2["inline_events"]
    assert res2["clean_text"] == "It's really late now..."


def test_mulberry_description_resolver():
    """
    Verifies Mulberry natural language description steering.
    Why this code exists:
    Silk Mulberry 1.5 allows controlling voices through natural language descriptions.
    This test verifies that descriptive parameters map to appropriate voice personas and SSML deltas.

    Tricky logic:
    Tests gender, accent, emotion, and pacing keyword resolution.

    TODO: Expand with multi-language accent test matrix.

    @danishansari-dev None
    @returns None
    """
    engine = ZaraVoiceEngine()

    # 1. Hindi female conversational companion
    voice_1, rate_1, pitch_1 = engine.resolve_voice_from_description(
        "a female 20s hindi voice, smooth timbre, casual pacing, warm emotion, like a companion"
    )
    assert voice_1 in ["zara-expressive", "zara-hinglish"]

    # 2. Deep male storyteller
    voice_2, rate_2, pitch_2 = engine.resolve_voice_from_description(
        "a male deep baritone voice, slow measured pacing, solemn register, like a storyteller"
    )
    assert voice_2 in ["zara-storyteller", "zara-podcast"]
    assert "-" in rate_2  # Slower pace

    # 3. British cheerful female
    voice_3, rate_3, pitch_3 = engine.resolve_voice_from_description(
        "a bright cheerful british female voice, fast energetic pacing"
    )
    assert voice_3 == "zara-playful"
    assert "+" in rate_3  # Faster pace


def test_dataset_preparation_manifest_pipeline():
    """
    Verifies the automated audio preprocessing, loudness normalization, and manifest pipeline.
    Why this code exists:
    Confirms that prepare_dataset.py successfully digests raw recordings and produces
    valid train, validation, and test JSONL manifests.

    Tricky logic:
    Generates synthetic WAV files, writes a metadata CSV, executes prepare_voice_dataset,
    and inspects the emitted JSONL files.

    TODO: Test handling of corrupted audio files and recovery.

    @danishansari-dev None
    @returns None
    """
    temp_dir = tempfile.mkdtemp(prefix="zara_test_dataset_")
    try:
        raw_dir = os.path.join(temp_dir, "raw")
        proc_dir = os.path.join(temp_dir, "processed")
        os.makedirs(raw_dir, exist_ok=True)

        # Generate 4 synthetic audio files
        csv_rows = []
        for i in range(1, 5):
            uid = f"sample_{i:03d}"
            wav_path = os.path.join(raw_dir, f"{uid}.wav")
            create_synthetic_wav(wav_path, duration_sec=2.5, sample_rate=24000)
            csv_rows.append({
                "id": uid,
                "audio_file": f"{uid}.wav",
                "text": f"[happy] Synthetic test turn number {i} <laugh>"
            })

        # Write metadata.csv
        import csv
        with open(os.path.join(raw_dir, "metadata.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "audio_file", "text"])
            writer.writeheader()
            writer.writerows(csv_rows)

        # Run pipeline
        res = prepare_voice_dataset(
            input_dir=raw_dir,
            output_dir=proc_dir,
            target_sr=24000,
            normalize_lufs=-23.0,
            train_ratio=0.75,
            val_ratio=0.25
        )

        assert res["status"] == "complete"
        assert res["total_items"] == 4
        assert res["train_count"] >= 2
        assert res["val_count"] >= 1

        # Check train manifest JSONL
        train_manifest = res["train_manifest"]
        assert os.path.exists(train_manifest)
        with open(train_manifest, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f]
            assert len(lines) == res["train_count"]
            sample = lines[0]
            assert "id" in sample
            assert "audio_filepath" in sample
            assert os.path.exists(sample["audio_filepath"])
            assert sample["sampling_rate"] == 24000
            assert sample["channels"] == 1
            assert sample["detected_tone"] == "happy"
            assert "laugh" in sample["inline_events"]

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_speech_lm_training_loop():
    """
    Verifies that the PyTorch speech training loop, forward pass, and checkpoint saving execute cleanly.
    Why this code exists:
    Confirms that train_voice.py executes a validated training step and persists checkpoints.

    Tricky logic:
    Runs a 2-epoch training run with batch collating and asserts loss values and checkpoint files.

    TODO: Benchmark GPU VRAM allocation when running on CUDA accelerator.

    @danishansari-dev None
    @returns None
    """
    temp_dir = tempfile.mkdtemp(prefix="zara_test_train_")
    try:
        manifest_path = os.path.join(temp_dir, "train_manifest.jsonl")
        ckpt_dir = os.path.join(temp_dir, "checkpoints")

        # Create mock manifest
        items = [
            {"id": f"s_{i}", "text": f"[happy] Test utterance {i} <laugh>", "duration": 2.0}
            for i in range(8)
        ]
        with open(manifest_path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item) + "\n")

        # Run training for 2 epochs
        summary = run_voice_training(
            config_path="",
            train_manifest=manifest_path,
            val_manifest=manifest_path,
            output_dir=ckpt_dir,
            max_epochs=2
        )

        assert summary["status"] == "completed"
        assert summary["total_epochs"] == 2
        assert summary["total_steps"] > 0
        assert os.path.exists(os.path.join(ckpt_dir, "checkpoint-epoch-1", "model_weights.pt"))
        assert os.path.exists(os.path.join(ckpt_dir, "checkpoint-epoch-2", "model_weights.pt"))
        assert os.path.exists(os.path.join(ckpt_dir, "final_model", "model_weights.pt"))

        # Verify loss values are real numbers (not NaN)
        for h in summary["history"]:
            assert not math.isnan(h["train_loss"])
            assert h["train_loss"] > 0.0

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_acoustic_pcm_evaluator_and_tag_adherence():
    """
    Verifies the objective acoustic evaluation metrics (SNR, duration) and tag adherence checker.
    Why this code exists:
    Guarantees that evaluate_voice.py correctly measures audio quality without crashing.

    Tricky logic:
    Generates a synthetic PCM buffer with known duration and verifies SNR computation.

    TODO: Add automated test for Whisper WER transcription pipeline.

    @danishansari-dev None
    @returns None
    """
    # 1. Test PCM audio analyzer
    sample_rate = 24000
    duration_target = 1.5
    n_samples = int(duration_target * sample_rate)
    pcm_frames = bytearray()
    for i in range(n_samples):
        val = int(12000.0 * math.sin(2.0 * math.pi * 300.0 * i / sample_rate))
        pcm_frames.extend(struct.pack('<h', val))

    dur, snr, peak = analyze_pcm_audio(bytes(pcm_frames), sample_rate=sample_rate)
    assert abs(dur - duration_target) < 0.05
    assert snr > 10.0
    assert 0.0 < peak <= 1.0

    # 2. Test tag adherence
    engine = ZaraVoiceEngine()
    adherence = verify_tag_adherence(engine, "[whisper] This is a secret turn <laugh>")
    assert adherence["adherence_passed"] is True
    assert adherence["detected_tone"] == "whisper"
    assert "whisper" not in adherence["cleaned_text"]
    assert "laugh" not in adherence["cleaned_text"]
    assert "[" not in adherence["cleaned_text"]
    assert "<" not in adherence["cleaned_text"]
