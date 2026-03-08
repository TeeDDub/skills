"""
음성 인식 → SRT 자막 생성 스크립트.

Usage:
    python3 transcribe.py <input_video> <output_srt> [--lang auto|ko|en]

전략:
1) mlx_whisper가 설치되어 있으면 우선 사용
2) 없으면 whisper CLI로 폴백
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def extract_audio(video_path: str, wav_path: str) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path],
        check=True,
    )


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def transcribe_with_mlx(wav_path: str, srt_path: str) -> int:
    import mlx_whisper  # type: ignore

    result = mlx_whisper.transcribe(
        wav_path,
        path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
        word_timestamps=True,
    )

    segments = result.get("segments", [])
    srt_lines: list[str] = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        text = str(seg.get("text", "")).strip()
        srt_lines.extend([str(i), f"{start} --> {end}", text, ""])

    Path(srt_path).write_text("\n".join(srt_lines), encoding="utf-8")
    return len(segments)


def transcribe_with_whisper_cli(video_path: str, srt_path: str, lang: str) -> int:
    whisper_bin = shutil.which("whisper")
    if not whisper_bin:
        raise RuntimeError("Neither mlx_whisper nor whisper CLI is available")

    out_dir = str(Path(srt_path).parent)
    stem = Path(srt_path).stem

    cmd = [
        whisper_bin,
        video_path,
        "--task",
        "transcribe",
        "--output_format",
        "srt",
        "--output_dir",
        out_dir,
        "--model",
        "turbo",
    ]
    if lang in {"ko", "en"}:
        cmd.extend(["--language", lang])

    subprocess.run(cmd, check=True)

    produced = Path(out_dir) / f"{Path(video_path).stem}.srt"
    target = Path(srt_path)

    if produced.exists() and produced != target:
        produced.replace(target)
    elif not target.exists():
        raise RuntimeError(f"Whisper output not found: {target}")

    text = target.read_text(encoding="utf-8", errors="ignore")
    return text.count(" --> ")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe video/audio into SRT subtitles")
    parser.add_argument("input_video", help="Input video file path")
    parser.add_argument("output_srt", help="Output SRT file path")
    parser.add_argument(
        "--lang",
        choices=["auto", "ko", "en"],
        default="auto",
        help="Language hint for whisper CLI (default: auto)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    video_path = args.input_video
    srt_path = args.output_srt
    lang_hint = args.lang

    if not os.path.exists(video_path):
        print(f"Error: {video_path} not found")
        sys.exit(1)

    Path(srt_path).parent.mkdir(parents=True, exist_ok=True)

    # 우선 mlx_whisper 경로 시도
    try:
        import mlx_whisper  # noqa: F401

        print("Transcribing with mlx_whisper...")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name
        try:
            extract_audio(video_path, wav_path)
            n = transcribe_with_mlx(wav_path, srt_path)
            print(f"Done (mlx_whisper): {n} segments -> {srt_path}")
            return
        finally:
            if os.path.exists(wav_path):
                os.remove(wav_path)
    except Exception as e:
        print(f"mlx_whisper path unavailable ({e}); fallback to whisper CLI...")

    # 폴백: whisper CLI
    try:
        n = transcribe_with_whisper_cli(video_path, srt_path, lang_hint)
        print(f"Done (whisper CLI): {n} segments -> {srt_path}")
    except Exception as e:
        print(f"Error: transcription failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
