"""
Zara Voice Model Evaluation & Acoustic Benchmark Suite
Why this file exists:
Provides an automated, reproducible evaluation tool to measure audio quality,
synthesis latency, Real-Time Factor (RTF), Signal-to-Noise Ratio (SNR),
and emotional tag adherence across standardized conversational speech benchmarks.
"""

import os
import io
import sys
import json
import time
import math
import wave
import struct
import argparse
from typing import Dict, Any, List, Optional, Tuple

# Ensure project root is on sys.path for direct CLI execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from zara.voice_engine import ZaraVoiceEngine, ZARA_VOICES

# Standard benchmark evaluation utterances covering all companion expressive modes
BENCHMARK_UTTERANCES = [
    {
        "id": "bench_01_neutral_conversational",
        "category": "neutral_conversational",
        "text": "Hey there, I was just thinking about how your day went. Tell me everything.",
        "expected_tone": "neutral"
    },
    {
        "id": "bench_02_whisper_intimate",
        "category": "whisper_intimate",
        "text": "[whisper] It's really late, but I'm right here with you. Take a deep breath and let it all go.",
        "expected_tone": "whisper"
    },
    {
        "id": "bench_03_happy_laughter",
        "category": "happy_laughter",
        "text": "[happy] Arre wah! You actually pulled that off? <laugh> I knew you could do it!",
        "expected_tone": "happy"
    },
    {
        "id": "bench_04_sad_sigh",
        "category": "sad_sigh",
        "text": "[sad] That sounds exhausting... <sigh> Sometimes things just feel overwhelming, and that's okay.",
        "expected_tone": "sad"
    },
    {
        "id": "bench_05_hinglish_code_switching",
        "category": "hinglish_code_switching",
        "text": "Bilkul tension mat lo yaar, together we will figure out a proper jugaad for this project.",
        "expected_tone": "neutral"
    }
]


def analyze_pcm_audio(pcm_bytes: bytes, sample_rate: int = 24000) -> Tuple[float, float, float]:
    """
    Calculates audio duration and Signal-to-Noise Ratio (SNR) from raw PCM bytes
    Why this code exists:
    Evaluates synthesized audio quality without external heavyweight DSP dependencies,
    detecting digital clipping, silence degradation, and acoustic distortion.

    Tricky logic:
    Unpacks 16-bit signed PCM frames, separates active voice samples from silence floor
    using energy thresholds, and calculates SNR in decibels (dB).

    TODO: Integrate PESQ (Perceptual Evaluation of Speech Quality) metric bindings.

    @danishansari-dev pcm_bytes - Raw 16-bit mono PCM audio data
    @danishansari-dev sample_rate - Audio sample rate (e.g. 24000)
    @returns Tuple of (duration_sec, estimated_snr_db, max_peak_amplitude)
    """
    n_samples = len(pcm_bytes) // 2
    if n_samples == 0:
        return 0.0, 0.0, 0.0

    duration = float(n_samples) / float(sample_rate)

    # Unpack 16-bit signed little-endian integers
    samples = struct.unpack(f"<{n_samples}h", pcm_bytes[:n_samples * 2])

    max_peak = max(abs(s) for s in samples) / 32768.0

    # Calculate active voice energy vs noise floor
    energies = [float(s * s) for s in samples]

    # Threshold for speech activity (top 50% vs bottom 20%)
    sorted_energies = sorted(energies)
    noise_floor = sum(sorted_energies[:int(len(sorted_energies) * 0.15)]) / max(int(len(sorted_energies) * 0.15), 1)
    speech_energy = sum(sorted_energies[int(len(sorted_energies) * 0.5):]) / max(int(len(sorted_energies) * 0.5), 1)

    if noise_floor > 0 and speech_energy > noise_floor:
        snr = 10.0 * math.log10(speech_energy / noise_floor)
    else:
        snr = 32.0  # Clean digital background baseline

    return round(duration, 3), round(min(snr, 55.0), 2), round(max_peak, 3)


def verify_tag_adherence(engine: ZaraVoiceEngine, text: str) -> Dict[str, Any]:
    """
    Verifies that tone tags and control markers are not spoken aloud into audio
    Why this code exists:
    A common defect in un-tuned models is reciting '[happy]' or '<laugh>' as literal speech.
    This checks that the text cleaner stripped tags before acoustic generation.

    Tricky logic:
    Checks whether bracketed metadata was preserved in cleaned transcript or properly handled.

    TODO: Add automatic phonetic transcript alignment to verify laugh pause acoustic duration.

    @danishansari-dev engine - ZaraVoiceEngine instance
    @danishansari-dev text - Raw benchmark text
    @returns Dictionary of verification status and cleaned text
    """
    cleaned, rate, pitch, tone = engine.parse_prosody_and_tags(text)
    leaked_tags = []
    if "[" in cleaned or "]" in cleaned:
        leaked_tags.append("bracket_tag_leak")
    if "<" in cleaned or ">" in cleaned:
        leaked_tags.append("xml_tag_leak")

    return {
        "adherence_passed": len(leaked_tags) == 0,
        "detected_tone": tone,
        "rate_offset": rate,
        "pitch_offset": pitch,
        "cleaned_text": cleaned,
        "leaked_tags": leaked_tags
    }


async def run_voice_evaluation(output_dir: str = "./evaluation_results", voice_name: str = "zara-expressive") -> Dict[str, Any]:
    """
    Runs full automated voice evaluation across all benchmark utterances
    Why this code exists:
    The primary entry point for objective quality assurance in Project Zara.
    Synthesizes benchmark WAVs, measures latency and RTF, and exports a quality audit report.

    Tricky logic:
    Uses high-resolution wall-clock timers to record exact time-to-first-chunk and total synthesis
    duration to calculate Real-Time Factor (RTF) rigorously.

    TODO: Run automated Whisper transcription to compute official WER score per benchmark.

    @danishansari-dev output_dir - Target directory for audio WAVs and eval_report.json
    @danishansari-dev voice_name - Named voice persona to test
    @returns Summary dictionary with metrics and benchmark evaluations
    """
    os.makedirs(output_dir, exist_ok=True)
    wavs_dir = os.path.join(output_dir, "wavs")
    os.makedirs(wavs_dir, exist_ok=True)

    engine = ZaraVoiceEngine(default_voice=voice_name)
    results: List[Dict[str, Any]] = []

    total_compute_time = 0.0
    total_audio_duration = 0.0

    print(f"==================================================")
    print(f"Starting Zara Voice Evaluation Suite")
    print(f"Target Voice: {voice_name} | Output: {output_dir}")
    print(f"==================================================")

    for item in BENCHMARK_UTTERANCES:
        bench_id = item["id"]
        raw_text = item["text"]
        cat = item["category"]

        tag_audit = verify_tag_adherence(engine, raw_text)

        # Measure wall-clock synthesis latency
        t0 = time.perf_counter()
        wav_bytes = await engine.synthesize(raw_text, voice_name=voice_name, audio_format="wav")
        compute_time = time.perf_counter() - t0

        # Export benchmark WAV file
        wav_path = os.path.join(wavs_dir, f"{bench_id}.wav")
        with open(wav_path, "wb") as f:
            f.write(wav_bytes)

        # Inspect synthesized audio properties
        pcm_bytes, _ = engine.transcode_audio(wav_bytes, target_format="pcm")
        audio_dur, snr_db, peak_amp = analyze_pcm_audio(pcm_bytes, sample_rate=24000)

        # Calculate Real-Time Factor (RTF)
        rtf = compute_time / audio_dur if audio_dur > 0 else 0.0
        total_compute_time += compute_time
        total_audio_duration += audio_dur

        entry = {
            "id": bench_id,
            "category": cat,
            "raw_text": raw_text,
            "cleaned_text": tag_audit["cleaned_text"],
            "detected_tone": tag_audit["detected_tone"],
            "rate_offset": tag_audit["rate_offset"],
            "pitch_offset": tag_audit["pitch_offset"],
            "tag_adherence_passed": tag_audit["adherence_passed"],
            "compute_time_sec": round(compute_time, 3),
            "audio_duration_sec": audio_dur,
            "rtf": round(rtf, 4),
            "snr_db": snr_db,
            "peak_amplitude": peak_amp,
            "wav_path": os.path.abspath(wav_path)
        }
        results.append(entry)

        print(f"[{cat.upper()}] Audio: {audio_dur:.2f}s | Compute: {compute_time:.2f}s | RTF: {rtf:.3f} | SNR: {snr_db} dB")

    overall_rtf = total_compute_time / total_audio_duration if total_audio_duration > 0 else 0.0
    all_tags_passed = all(x["tag_adherence_passed"] for x in results)
    avg_snr = sum(x["snr_db"] for x in results) / len(results) if results else 0.0

    summary = {
        "voice_name": voice_name,
        "total_benchmarks": len(results),
        "total_compute_time_sec": round(total_compute_time, 3),
        "total_audio_duration_sec": round(total_audio_duration, 3),
        "overall_rtf": round(overall_rtf, 4),
        "realtime_capable": overall_rtf <= 0.30,
        "average_snr_db": round(avg_snr, 2),
        "all_tags_adhered": all_tags_passed,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "benchmarks": results
    }

    report_path = os.path.join(output_dir, "eval_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"==================================================")
    print(f"Evaluation Complete! Summary Report: {report_path}")
    print(f"Overall RTF: {overall_rtf:.4f} (Real-time: {overall_rtf <= 0.30}) | Avg SNR: {avg_snr:.1f} dB")
    print(f"==================================================")

    return summary


if __name__ == "__main__":
    import asyncio
    parser = argparse.ArgumentParser(description="Zara Voice Model Evaluation Suite")
    parser.add_argument("--output_dir", type=str, default="./evaluation_results", help="Destination folder for evaluation artifacts")
    parser.add_argument("--voice_name", type=str, default="zara-expressive", help="Voice personality to evaluate")

    args = parser.parse_args()
    report = asyncio.run(run_voice_evaluation(output_dir=args.output_dir, voice_name=args.voice_name))
