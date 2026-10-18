"""
Zara Voice Dataset Preparation Pipeline
Why this file exists:
Voice models require clean, standardized, mono 24 kHz audio with normalized loudness
and aligned transcripts. This script ingests raw recordings, normalizes sample rates
and audio levels, trims silence, validates metadata, and generates train/val/test manifests.
"""

import os
import io
import re
import csv
import json
import wave
import struct
import math
import argparse
from typing import Dict, Any, List, Optional, Tuple

try:
    from pydub import AudioSegment
    from pydub.silence import detect_leading_silence
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


def inspect_audio_file(filepath: str) -> Tuple[int, int, float]:
    """
    Inspects a WAV file header directly using standard library wave module
    Why this code exists:
    Provides a zero-dependency fallback to inspect audio metadata when heavy
    audio libraries like pydub or soundfile are unavailable in minimal environments.

    Tricky logic:
    Reads channel count, sample width, frame rate, and calculates duration in seconds
    directly from binary header frames without loading audio into memory.

    TODO: Support direct MP3/OGG container header parsing without external decoders.

    @danishansari-dev filepath - Path to audio file
    @returns Tuple of (channels, sample_rate, duration_seconds)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Audio file not found: {filepath}")

    if filepath.lower().endswith(".wav"):
        try:
            with wave.open(filepath, 'rb') as wf:
                channels = wf.getnchannels()
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                duration = float(n_frames) / float(sample_rate) if sample_rate > 0 else 0.0
                return channels, sample_rate, duration
        except Exception:
            pass

    if PYDUB_AVAILABLE:
        try:
            seg = AudioSegment.from_file(filepath)
            return seg.channels, seg.frame_rate, len(seg) / 1000.0
        except Exception as e:
            raise ValueError(f"Failed to read audio file {filepath}: {e}")

    # Fallback default
    return 1, 24000, 0.0


def trim_audio_silence(seg: 'AudioSegment', silence_threshold: float = -45.0) -> 'AudioSegment':
    """
    Trims leading and trailing silence from an AudioSegment
    Why this code exists:
    Long silence padding at the start or end of audio clips wastes GPU memory,
    slows down attention matrix computation, and causes model stuttering.

    Tricky logic:
    Detects silence below silence_threshold dBFS from the front, reverses the segment,
    trims trailing silence, reverses back, and adds a natural 50ms room tone cushion.

    TODO: Implement adaptive noise-floor estimation instead of fixed dBFS threshold.

    @danishansari-dev seg - Pydub AudioSegment
    @danishansari-dev silence_threshold - dBFS threshold below which audio is considered silent
    @returns Trimmed AudioSegment
    """
    if not PYDUB_AVAILABLE:
        return seg

    start_trim = detect_leading_silence(seg, silence_threshold=silence_threshold)
    end_trim = detect_leading_silence(seg.reverse(), silence_threshold=silence_threshold)
    duration = len(seg)

    # If the whole clip is silent, return as is
    if start_trim >= duration:
        return seg

    trimmed = seg[start_trim:duration - end_trim]
    # Preserve 50ms cushion on both ends to avoid clipping vocal transients
    pad = AudioSegment.silent(duration=50)
    return pad + trimmed + pad


def estimate_lufs(seg: 'AudioSegment') -> float:
    """
    Calculates root mean square (RMS) and estimates LUFS loudness
    Why this code exists:
    Speech synthesis training requires consistent acoustic volume so gradient descent
    does not bias weights toward unusually loud clips.

    Tricky logic:
    Computes RMS amplitude over 16-bit PCM samples and converts to decibels relative
    to full scale (dBFS), which closely correlates with integrated LUFS for conversational speech.

    TODO: Integrate ITU-R BS.1770-4 K-weighting filter for certified EBU R128 compliance.

    @danishansari-dev seg - Pydub AudioSegment
    @returns Estimated loudness in LUFS / dBFS
    """
    if not PYDUB_AVAILABLE:
        return -23.0
    return float(seg.dBFS) if seg.dBFS != float('-inf') else -70.0


def normalize_audio_loudness(seg: 'AudioSegment', target_lufs: float = -23.0) -> 'AudioSegment':
    """
    Normalizes an audio segment to a target LUFS / dBFS level
    Why this code exists:
    Standardizes volume to -23 LUFS (broadcast speech standard) across heterogeneous microphones.

    Tricky logic:
    Calculates the delta between target and current dBFS and applies gain, capping maximum
    gain adjustment to +15 dB to prevent amplifying extreme background hiss.

    TODO: Add dynamic range compression for highly dynamic speaker outbursts.

    @danishansari-dev seg - Pydub AudioSegment
    @danishansari-dev target_lufs - Target loudness level (e.g. -23.0)
    @returns Gain-normalized AudioSegment
    """
    if not PYDUB_AVAILABLE:
        return seg
    current = estimate_lufs(seg)
    if current <= -60.0:
        return seg  # Do not amplify virtually silent clips
    gain = target_lufs - current
    gain = max(min(gain, 15.0), -15.0)  # Bound gain to +/- 15 dB
    return seg.apply_gain(gain)


def parse_transcript_metadata(text: str) -> Dict[str, Any]:
    """
    Extracts emotional tone tags and clean transcript from tagged text
    Why this code exists:
    Models like Silk Muga and Zara conditioning use bracketed tone tags ([happy], [whisper])
    and inline vocalizations (<laugh>, <sigh>). We must index these tags separately in manifests.

    Tricky logic:
    Uses regular expressions to parse leading brackets while maintaining inline paralinguistics.

    TODO: Support automated sentiment tag generation from untagged transcripts.

    @danishansari-dev text - Raw transcript with potential tags
    @returns Dictionary with clean_text, detected_tone, and inline_events
    """
    raw = text.strip()
    tone = "neutral"
    tone_match = re.match(r'^\s*\[(happy|excited|sad|angry|neutral|whisper|softly|intimate)\]\s*', raw, re.IGNORECASE)
    if tone_match:
        tone = tone_match.group(1).lower()
        raw = raw[tone_match.end():].strip()

    inline_events = re.findall(r'<\s*([a-zA-Z_]+)\s*>', raw)

    # Clean text without any bracketed tags
    clean = re.sub(r'\[.*?\]', '', raw)
    clean = re.sub(r'<.*?>', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    return {
        "raw_text": text.strip(),
        "clean_text": clean if clean else raw,
        "detected_tone": tone,
        "inline_events": [e.lower() for e in inline_events]
    }


def process_single_audio(input_path: str, output_path: str, target_sr: int = 24000, target_lufs: float = -23.0) -> Dict[str, Any]:
    """
    Processes an individual audio file and exports standardized 24 kHz WAV
    Why this code exists:
    Converts arbitrary user input recordings into the exact format required by the model.

    Tricky logic:
    Downmixes to mono, resamples to target_sr (24000 Hz), trims silence, normalizes loudness,
    and writes 16-bit little-endian PCM WAV.

    TODO: Add automatic audio clipping restoration for distorted audio peaks.

    @danishansari-dev input_path - Source audio file path
    @danishansari-dev output_path - Target output WAV path
    @danishansari-dev target_sr - Target sample rate (24000 Hz)
    @danishansari-dev target_lufs - Target loudness (-23.0)
    @returns Dictionary of processed audio properties (duration, lufs, channels)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if PYDUB_AVAILABLE:
        seg = AudioSegment.from_file(input_path)
        seg = seg.set_channels(1)
        seg = seg.set_frame_rate(target_sr)
        seg = trim_audio_silence(seg)
        seg = normalize_audio_loudness(seg, target_lufs)

        # Export as 16-bit 24kHz mono WAV
        seg.export(output_path, format="wav", parameters=["-ac", "1", "-ar", str(target_sr)])
        duration = len(seg) / 1000.0
        final_lufs = estimate_lufs(seg)
        return {
            "duration": round(duration, 3),
            "sampling_rate": target_sr,
            "channels": 1,
            "lufs": round(final_lufs, 2),
            "status": "success"
        }
    else:
        # Fallback when pydub is missing: copy or standard wave check
        import shutil
        shutil.copyfile(input_path, output_path)
        ch, sr, dur = inspect_audio_file(output_path)
        return {
            "duration": round(dur, 3),
            "sampling_rate": sr,
            "channels": ch,
            "lufs": -23.0,
            "status": "copied_raw"
        }


def prepare_voice_dataset(
    input_dir: str,
    output_dir: str,
    target_sr: int = 24000,
    normalize_lufs: float = -23.0,
    train_ratio: float = 0.85,
    val_ratio: float = 0.10,
    speaker_id: str = "zara",
    language: str = "en-IN"
) -> Dict[str, Any]:
    """
    Prepares complete voice dataset directory and generates train/val/test manifests
    Why this code exists:
    Automates end-to-end dataset preparation for model training and Google Colab execution.

    Tricky logic:
    Reads metadata CSV/JSONL, processes corresponding audio files, filters invalid durations
    (< 1.0s or > 20s), splits deterministically into train/val/test partitions, and outputs JSONL manifests.

    TODO: Support automated phonetic forced alignment using CTC or WhisperX.

    @danishansari-dev input_dir - Directory containing raw audio and metadata.csv
    @danishansari-dev output_dir - Target directory for processed dataset
    @danishansari-dev target_sr - Target sample rate (default 24000)
    @danishansari-dev normalize_lufs - Target LUFS loudness (default -23.0)
    @danishansari-dev train_ratio - Fraction for training (default 0.85)
    @danishansari-dev val_ratio - Fraction for validation (default 0.10)
    @returns Summary dictionary with counts and paths
    """
    os.makedirs(output_dir, exist_ok=True)
    wavs_out_dir = os.path.join(output_dir, "wavs")
    os.makedirs(wavs_out_dir, exist_ok=True)

    # 1. Locate metadata file (metadata.csv or metadata.jsonl)
    meta_csv = os.path.join(input_dir, "metadata.csv")
    meta_jsonl = os.path.join(input_dir, "metadata.jsonl")

    records: List[Dict[str, str]] = []
    if os.path.exists(meta_csv):
        with open(meta_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    elif os.path.exists(meta_jsonl):
        with open(meta_jsonl, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    else:
        # Auto-discover audio files if no explicit metadata exists
        print(f"No metadata file found in {input_dir}. Auto-discovering audio files...")
        valid_exts = {".wav", ".mp3", ".ogg", ".flac", ".m4a"}
        idx = 0
        for root, _, files in os.walk(input_dir):
            for file in sorted(files):
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_exts:
                    idx += 1
                    name = os.path.splitext(file)[0]
                    records.append({
                        "id": name,
                        "audio_file": file,
                        "text": f"Utterance sample {idx} from {name}."
                    })

    print(f"Discovered {len(records)} candidate audio records.")

    processed_items: List[Dict[str, Any]] = []
    skipped_count = 0

    for idx, rec in enumerate(records):
        item_id = rec.get("id", f"sample_{idx:05d}")
        audio_filename = rec.get("audio_file") or rec.get("audio_filepath") or f"{item_id}.wav"
        raw_text = rec.get("text", "")

        src_audio_path = os.path.join(input_dir, audio_filename)
        if not os.path.exists(src_audio_path):
            if os.path.exists(audio_filename):
                src_audio_path = audio_filename
            else:
                src_audio_path = os.path.join(input_dir, "wavs", audio_filename)

        if not os.path.exists(src_audio_path):
            skipped_count += 1
            continue

        target_wav_path = os.path.join(wavs_out_dir, f"{item_id}.wav")

        try:
            audio_props = process_single_audio(
                src_audio_path,
                target_wav_path,
                target_sr=target_sr,
                target_lufs=normalize_lufs
            )
            dur = audio_props["duration"]

            if dur < 1.0 or dur > 20.0:
                skipped_count += 1
                if os.path.exists(target_wav_path):
                    os.remove(target_wav_path)
                continue

            text_props = parse_transcript_metadata(raw_text)

            manifest_entry = {
                "id": item_id,
                "audio_filepath": os.path.abspath(target_wav_path),
                "duration": dur,
                "sampling_rate": target_sr,
                "channels": 1,
                "text": text_props["raw_text"],
                "clean_text": text_props["clean_text"],
                "speaker_id": speaker_id,
                "language": language,
                "detected_tone": text_props["detected_tone"],
                "inline_events": text_props["inline_events"],
                "lufs": audio_props["lufs"]
            }
            processed_items.append(manifest_entry)

        except Exception as e:
            print(f"Error processing {src_audio_path}: {e}")
            skipped_count += 1

    total_valid = len(processed_items)
    print(f"Processed {total_valid} valid audio items (Skipped {skipped_count}).")

    if total_valid == 0:
        return {"total_items": 0, "status": "no_valid_items"}

    # 2. Split dataset into train, val, and test
    n_train = int(total_valid * train_ratio)
    n_val = int(total_valid * val_ratio)
    train_items = processed_items[:n_train]
    val_items = processed_items[n_train:n_train + n_val]
    test_items = processed_items[n_train + n_val:]

    # Fallback: ensure validation set has at least 1 item if total >= 2
    if len(val_items) == 0 and total_valid >= 2:
        val_items.append(train_items.pop())

    # 3. Write manifests
    train_manifest = os.path.join(output_dir, "train_manifest.jsonl")
    val_manifest = os.path.join(output_dir, "val_manifest.jsonl")
    test_manifest = os.path.join(output_dir, "test_manifest.jsonl")

    def _write_jsonl(path: str, items: List[Dict[str, Any]]):
        with open(path, 'w', encoding='utf-8') as out:
            for item in items:
                out.write(json.dumps(item, ensure_ascii=False) + "\n")

    _write_jsonl(train_manifest, train_items)
    _write_jsonl(val_manifest, val_items)
    _write_jsonl(test_manifest, test_items)

    summary = {
        "total_items": total_valid,
        "train_count": len(train_items),
        "val_count": len(val_items),
        "test_count": len(test_items),
        "train_manifest": train_manifest,
        "val_manifest": val_manifest,
        "test_manifest": test_manifest,
        "status": "complete"
    }

    summary_path = os.path.join(output_dir, "dataset_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zara Voice Dataset Preprocessing Pipeline")
    parser.add_argument("--input_dir", type=str, required=True, help="Input directory containing raw audio")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for processed dataset")
    parser.add_argument("--target_sr", type=int, default=24000, help="Target sample rate (Hz)")
    parser.add_argument("--normalize_lufs", type=float, default=-23.0, help="Target loudness level in LUFS")
    parser.add_argument("--speaker_id", type=str, default="zara", help="Speaker identifier")
    parser.add_argument("--language", type=str, default="hi-IN", help="Language code")

    args = parser.parse_args()
    res = prepare_voice_dataset(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        target_sr=args.target_sr,
        normalize_lufs=args.normalize_lufs,
        speaker_id=args.speaker_id,
        language=args.language
    )
    print("Dataset Preparation Result:", json.dumps(res, indent=2))
