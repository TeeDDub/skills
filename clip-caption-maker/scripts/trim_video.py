"""
영상 트리밍/복사를 수행하는 스크립트.

Usage:
    python3 trim_video.py <input> <output> --start <ts> --end <ts> [--mode fast|precise]
    python3 trim_video.py <input> <output> --full-copy

fast 모드: ffmpeg copy(-c copy)
precise 모드: libx264 재인코드 (preset=medium, crf=18, aac)
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


TIME_PATTERN = re.compile(r"^\d{1,2}:\d{2}(:\d{2}(\.\d{1,3})?)?$")


def parse_timecode(value: str) -> float:
    if not TIME_PATTERN.match(value):
        raise ValueError("시간 형식은 HH:MM:SS(.ms) 또는 MM:SS여야 합니다.")
    parts = value.split(":")
    parts = [float(p) for p in parts]
    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    hours, minutes, seconds = parts if len(parts) == 3 else (0.0, parts[0], parts[1])
    return hours * 3600 + minutes * 60 + seconds


def build_trim_command(
    input_path: str,
    output_path: str,
    start: str,
    end: str,
    mode: str,
) -> list[str]:
    base = ["ffmpeg", "-y", "-ss", start, "-to", end, "-i", input_path]
    if mode == "fast":
        return base + ["-c", "copy", output_path]
    return base + [
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-c:a",
        "aac",
        output_path,
    ]


def build_full_copy_command(input_path: str, output_path: str) -> list[str]:
    return ["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path]


def run_command(cmd: list[str]) -> None:
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 실행 실패 (exit {result.returncode})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trim or copy a video using ffmpeg.")
    parser.add_argument("input", help="Input video file path")
    parser.add_argument("output", help="Output video file path")
    parser.add_argument("--start", help="Start timestamp (HH:MM:SS or MM:SS)")
    parser.add_argument("--end", help="End timestamp (HH:MM:SS or MM:SS)")
    parser.add_argument(
        "--mode",
        choices=["fast", "precise"],
        default="fast",
        help="Trimming mode (default: fast)",
    )
    parser.add_argument(
        "--full-copy",
        action="store_true",
        help="Copy the entire video without trimming.",
    )
    return parser.parse_args()


def validate_paths(input_path: str, output_path: str) -> None:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")
    out_dir = Path(output_path).parent
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)


def main() -> None:
    args = parse_args()
    input_path = args.input
    output_path = args.output
    start = args.start
    end = args.end
    mode = args.mode
    full_copy = args.full_copy

    try:
        validate_paths(input_path, output_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if full_copy:
        if start or end:
            print("Error: --full-copy 옵션과 --start/--end는 함께 사용할 수 없습니다.", file=sys.stderr)
            sys.exit(1)
        cmd = build_full_copy_command(input_path, output_path)
    else:
        if not start or not end:
            print("Error: --start와 --end를 모두 지정해야 합니다.", file=sys.stderr)
            sys.exit(1)
        try:
            start_sec = parse_timecode(start)
            end_sec = parse_timecode(end)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        if start_sec >= end_sec:
            print("Error: 시작 시간이 종료 시간보다 빠르거나 같을 수 없습니다.", file=sys.stderr)
            sys.exit(1)
        cmd = build_trim_command(input_path, output_path, start, end, mode)

    try:
        run_command(cmd)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Saved trimmed video to {output_path}")


if __name__ == "__main__":
    main()
