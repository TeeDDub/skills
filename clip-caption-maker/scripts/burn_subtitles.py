"""
자막을 영상에 burn-in (하드코딩) 하는 스크립트.

Usage:
    python3 burn_subtitles.py <input_video> <input_srt> <output_video>
      [--fontsize 40] [--font "/path/to/font.ttf"]
      [--subtitle-color "#FFFFFF"] [--outline-color "#000000"]
      [--position bottom|top] [--text-aware]
      [--onscreen-srt onscreen.ko.srt]
      [--extract-onscreen-text-to onscreen.original.srt]
      [--extract-onscreen-text-only]
      [--onscreen-color "#FFD400"] [--onscreen-position top]

기본 전략:
1) ffmpeg subtitles 필터(libass) 사용 시도
2) 실패하거나 미지원이면 moviepy + PIL 폴백

text-aware 모드:
- 영상 내 기존 텍스트/자막과 겹침을 줄이기 위해
  - 기본 위치를 top으로
  - 기본 자막 색을 cyan(#00E5FF)으로 자동 변경

온스크린 텍스트 처리:
- 이 스크립트는 OCR 추출까지만 담당한다 (번역은 에이전트가 컨텍스트 기반으로 수행)
- --extract-onscreen-text-to 로 OCR 텍스트 SRT 생성
- --onscreen-srt 로 번역된 온스크린 SRT를 오버레이
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

NOTO_SANS_KR_URL = "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
FONT_INSTALL_DIR = Path.home() / "Library" / "Fonts"
DEFAULT_FONT_FILE = FONT_INSTALL_DIR / "NotoSansKR[wght].ttf"

NAMED_COLORS = {
    "white": "#FFFFFF",
    "black": "#000000",
    "yellow": "#FFD400",
    "cyan": "#00E5FF",
    "green": "#00FF66",
    "magenta": "#FF4DFF",
    "orange": "#FF8A00",
}


def normalize_hex(color: str) -> str:
    c = color.strip().lower()
    c = NAMED_COLORS.get(c, c)
    if c.startswith("#"):
        c = c[1:]
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        raise ValueError(f"Invalid color: {color}")
    int(c, 16)
    return f"#{c.upper()}"


def hex_to_rgb_tuple(color: str) -> tuple[int, int, int]:
    c = normalize_hex(color)[1:]
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def hex_to_ass_bbggrr(color: str) -> str:
    """#RRGGBB -> ASS color format &H00BBGGRR"""
    c = normalize_hex(color)[1:]
    rr, gg, bb = c[0:2], c[2:4], c[4:6]
    return f"&H00{bb}{gg}{rr}"


def ensure_noto_sans_kr() -> str:
    """가능하면 Noto Sans KR 폰트 파일 경로를 반환한다."""
    if DEFAULT_FONT_FILE.exists():
        return str(DEFAULT_FONT_FILE)

    print("Noto Sans KR 폰트를 다운로드합니다...")
    FONT_INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(NOTO_SANS_KR_URL, str(DEFAULT_FONT_FILE))

    fc_cache = shutil.which("fc-cache")
    if fc_cache:
        subprocess.run([fc_cache, "-f"], capture_output=True)

    print(f"Noto Sans KR 설치 완료 → {DEFAULT_FONT_FILE}")
    return str(DEFAULT_FONT_FILE)


def check_libass() -> bool:
    """ffmpeg에 subtitles 필터(libass)가 있는지 확인."""
    try:
        result = subprocess.run(["ffmpeg", "-filters"], capture_output=True, text=True)
        return " subtitles " in result.stdout or "subtitles" in result.stdout
    except Exception:
        return False


def ffmpeg_escape_path(path: str) -> str:
    return path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def burn_with_ffmpeg(
    video: str,
    srt: str,
    output: str,
    fontsize: int,
    subtitle_color: str,
    outline_color: str,
    position: str,
    onscreen_srt: str | None = None,
    onscreen_fontsize: int = 34,
    onscreen_color: str = "#FFD400",
    onscreen_outline_color: str = "#000000",
    onscreen_position: str = "top",
) -> bool:
    alignment = "8" if position == "top" else "2"
    style_main = (
        f"Fontsize={fontsize},"
        f"PrimaryColour={hex_to_ass_bbggrr(subtitle_color)},"
        f"OutlineColour={hex_to_ass_bbggrr(outline_color)},"
        "Outline=2,"
        f"Alignment={alignment},"
        "MarginV=56"
    )

    srt_escaped = ffmpeg_escape_path(srt)
    vf_parts = [f"subtitles=filename='{srt_escaped}':force_style='{style_main}'"]

    if onscreen_srt:
        alignment_os = "8" if onscreen_position == "top" else "2"
        style_os = (
            f"Fontsize={onscreen_fontsize},"
            f"PrimaryColour={hex_to_ass_bbggrr(onscreen_color)},"
            f"OutlineColour={hex_to_ass_bbggrr(onscreen_outline_color)},"
            "Outline=2,"
            f"Alignment={alignment_os},"
            "MarginV=92"
        )
        os_escaped = ffmpeg_escape_path(onscreen_srt)
        vf_parts.append(f"subtitles=filename='{os_escaped}':force_style='{style_os}'")

    vf = ",".join(vf_parts)
    cmd = ["ffmpeg", "-y", "-i", video, "-vf", vf, "-c:a", "copy", output]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-800:])
    return result.returncode == 0


def render_text_image(
    text: str,
    font_path: str,
    font_size: int,
    max_width: int,
    color: tuple[int, int, int],
    stroke_color: tuple[int, int, int],
    stroke_width: int = 2,
):
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np

    pil_font = ImageFont.truetype(font_path, font_size)
    try:
        pil_font.set_variation_by_axes([500])
    except Exception:
        pass

    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=pil_font, stroke_width=stroke_width)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    if text_w > max_width:
        import textwrap

        avg_char_w = max(text_w / max(len(text), 1), 1)
        wrap_width = max(int(max_width / avg_char_w), 1)
        text = textwrap.fill(text, width=wrap_width)
        bbox = draw.multiline_textbbox((0, 0), text, font=pil_font, stroke_width=stroke_width)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

    padding = int(font_size * 0.4)
    img = Image.new("RGBA", (text_w + stroke_width * 2, text_h + padding), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.multiline_text(
        (stroke_width, stroke_width),
        text,
        font=pil_font,
        fill=color,
        stroke_fill=stroke_color,
        stroke_width=stroke_width,
        align="center",
    )
    return np.array(img)


def burn_with_moviepy(
    video: str,
    srt: str,
    output: str,
    fontsize: int,
    font: str,
    subtitle_color: str,
    outline_color: str,
    position: str,
    onscreen_srt: str | None = None,
    onscreen_fontsize: int = 34,
    onscreen_color: str = "#FFD400",
    onscreen_outline_color: str = "#000000",
    onscreen_position: str = "top",
) -> bool:
    try:
        from moviepy import CompositeVideoClip, ImageClip, VideoFileClip
    except ImportError as e:
        raise RuntimeError(
            "moviepy가 필요합니다. 예: uv venv .venv-clip && "
            "source .venv-clip/bin/activate && uv pip install moviepy pillow numpy imageio imageio-ffmpeg"
        ) from e

    clip = VideoFileClip(video)
    margin = int(clip.h * 0.05)
    max_width = int(clip.w * 0.85)

    def make_text_clips(
        segments: list[dict],
        this_fontsize: int,
        this_color: str,
        this_outline: str,
        this_position: str,
    ) -> list:
        txt_clips = []
        fill = hex_to_rgb_tuple(this_color)
        stroke = hex_to_rgb_tuple(this_outline)
        for seg in segments:
            img_array = render_text_image(
                seg["text"],
                font,
                this_fontsize,
                max_width,
                color=fill,
                stroke_color=stroke,
                stroke_width=2,
            )
            txt = ImageClip(img_array, transparent=True)
            txt_y = margin if this_position == "top" else clip.h - img_array.shape[0] - margin
            txt = txt.with_position(("center", txt_y)).with_start(seg["start"]).with_end(seg["end"])
            txt_clips.append(txt)
        return txt_clips

    all_clips = [clip]
    all_clips.extend(make_text_clips(parse_srt(srt), fontsize, subtitle_color, outline_color, position))

    if onscreen_srt:
        all_clips.extend(
            make_text_clips(
                parse_srt(onscreen_srt),
                onscreen_fontsize,
                onscreen_color,
                onscreen_outline_color,
                onscreen_position,
            )
        )

    final = CompositeVideoClip(all_clips)
    final.write_videofile(output, codec="libx264", audio_codec="aac", logger="bar")
    clip.close()
    final.close()
    return True


def parse_srt(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    segments = []
    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        time_line = lines[1]
        text = "\n".join(lines[2:]).strip()
        if not text or " --> " not in time_line:
            continue
        start_str, end_str = time_line.split(" --> ")
        segments.append({
            "start": srt_time_to_seconds(start_str.strip()),
            "end": srt_time_to_seconds(end_str.strip()),
            "text": text,
        })
    return segments


def write_srt(path: str, segments: list[dict]) -> None:
    lines: list[str] = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{seconds_to_srt_time(seg['start'])} --> {seconds_to_srt_time(seg['end'])}")
        lines.append(seg["text"])
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def srt_time_to_seconds(t: str) -> float:
    parts = t.replace(",", ".").split(":")
    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])


def seconds_to_srt_time(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _texts_similar(a: str, b: str, threshold: float = 0.85) -> bool:
    if not a or not b:
        return a == b
    return difflib.SequenceMatcher(None, a, b).ratio() >= threshold


def extract_onscreen_text_srt(
    video: str,
    output_srt: str,
    sample_interval: float = 1.0,
    ocr_langs: list[str] | None = None,
    min_conf: float = 0.4,
    min_text_len: int = 2,
    diff_threshold: float = 0.02,
    watermark_ratio: float = 0.7,
) -> int:
    """프레임 변화 감지 + EasyOCR로 온스크린 텍스트 SRT 생성.

    - 기본 1초 간격 샘플링 + 프레임 diff로 변화 시점만 OCR (가사 MV는 --ocr-interval-sec 0.3 권장)
    - 워터마크/로고 자동 필터링 (빈도 기반)
    - EasyOCR: 스타일 텍스트(가사 자막 등)에 강함
    """
    try:
        import cv2  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "opencv-python이 필요합니다: uv pip install opencv-python"
        ) from e
    try:
        import easyocr  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "easyocr가 필요합니다: uv pip install easyocr"
        ) from e

    if ocr_langs is None:
        ocr_langs = ["en"]

    reader = easyocr.Reader(ocr_langs, gpu=False)

    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = (total_frames / fps) if total_frames > 0 else 0
    step = max(int(fps * sample_interval), 1)

    raw_segments: list[dict] = []
    prev_gray = None
    prev_text = ""
    text_freq: dict[str, int] = {}
    ocr_frame_count = 0

    frame_idx = 0
    while frame_idx < total_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, frame = cap.read()
        if not ok or frame is None:
            frame_idx += step
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 프레임 변화 감지: 변화 없으면 이전 세그먼트 연장
        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            change_ratio = float((diff > 30).sum()) / diff.size
            if change_ratio < diff_threshold:
                if raw_segments:
                    raw_segments[-1]["end"] = min(
                        frame_idx / fps + sample_interval,
                        duration or frame_idx / fps + sample_interval,
                    )
                prev_gray = gray
                frame_idx += step
                continue

        prev_gray = gray

        # 리사이즈 (OCR 속도 최적화)
        h, w = frame.shape[:2]
        if w > 1280:
            scale = 1280 / w
            frame = cv2.resize(frame, (1280, int(h * scale)))

        # EasyOCR 실행
        results = reader.readtext(frame)
        ocr_frame_count += 1
        texts: list[str] = []
        for _bbox, text, conf in results:
            text = text.strip()
            if conf >= min_conf and len(text) >= min_text_len:
                texts.append(text)
                text_freq[text] = text_freq.get(text, 0) + 1

        merged = "\n".join(texts)

        if merged and not _texts_similar(merged, prev_text):
            start = frame_idx / fps
            end = min(start + sample_interval, duration or start + sample_interval)
            raw_segments.append({"start": start, "end": end, "text": merged})
            prev_text = merged
        elif merged and _texts_similar(merged, prev_text) and raw_segments:
            raw_segments[-1]["end"] = min(
                frame_idx / fps + sample_interval,
                duration or frame_idx / fps + sample_interval,
            )

        frame_idx += step

    cap.release()
    print(f"[onscreen] OCR ran on {ocr_frame_count} frames (of {total_frames // max(step, 1)} sampled)")

    # 워터마크 필터링: OCR 실행 프레임의 70% 이상 등장 텍스트 제거
    if raw_segments and ocr_frame_count > 0:
        watermarks = {
            t for t, c in text_freq.items()
            if c / ocr_frame_count >= watermark_ratio
        }
        if watermarks:
            print(f"[onscreen] Filtered watermarks: {watermarks}")
            filtered: list[dict] = []
            for seg in raw_segments:
                lines = [l for l in seg["text"].split("\n") if l.strip() not in watermarks]
                if lines:
                    seg["text"] = "\n".join(lines)
                    filtered.append(seg)
            raw_segments = filtered

    # 연속 동일(유사) 텍스트 병합
    if raw_segments:
        compact: list[dict] = [raw_segments[0]]
        for seg in raw_segments[1:]:
            prev = compact[-1]
            if _texts_similar(seg["text"], prev["text"]) and abs(seg["start"] - prev["end"]) <= sample_interval * 2:
                prev["end"] = seg["end"]
            else:
                compact.append(seg)
        raw_segments = compact

    write_srt(output_srt, raw_segments)
    return len(raw_segments)


def main() -> None:
    parser = argparse.ArgumentParser(description="Burn subtitles into video")
    parser.add_argument("video", help="Input video file")
    parser.add_argument("srt", help="Input SRT subtitle file")
    parser.add_argument("output", help="Output video file")

    parser.add_argument("--fontsize", type=int, default=40)
    parser.add_argument("--font", default=None, help="Font file path or name")
    parser.add_argument("--subtitle-color", default="#FFFFFF", help="Subtitle color (hex or name)")
    parser.add_argument("--outline-color", default="#000000", help="Outline color (hex or name)")
    parser.add_argument("--position", choices=["top", "bottom"], default="bottom")
    parser.add_argument("--text-aware", action="store_true", help="기존 영상 텍스트와 겹침 방지 (상단+강조색)")

    # 온스크린 텍스트
    parser.add_argument("--onscreen-srt", default=None, help="번역된 온스크린 SRT 경로")
    parser.add_argument("--extract-onscreen-text-to", default=None, help="OCR 온스크린 추출 결과 SRT 경로")
    parser.add_argument("--extract-onscreen-text-only", action="store_true", help="OCR 추출만 수행하고 종료")
    parser.add_argument("--ocr-lang", default="en", help="EasyOCR language codes, comma-separated (default: en)")
    parser.add_argument("--ocr-interval-sec", type=float, default=1.0, help="OCR sampling interval seconds (default: 1.0, 가사MV는 0.3 권장)")
    parser.add_argument("--ocr-min-conf", type=float, default=0.4, help="OCR confidence threshold 0-1 (default: 0.4)")

    parser.add_argument("--onscreen-color", default="#FFD400", help="온스크린 번역 텍스트 색")
    parser.add_argument("--onscreen-outline-color", default="#000000", help="온스크린 번역 외곽선 색")
    parser.add_argument("--onscreen-position", choices=["top", "bottom"], default="top")
    parser.add_argument("--onscreen-fontsize", type=int, default=34)

    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"Error: {args.video} not found")
        sys.exit(1)

    if not args.extract_onscreen_text_only and not os.path.exists(args.srt):
        print(f"Error: main subtitle SRT not found for burn mode → {args.srt}")
        sys.exit(1)

    subtitle_color = args.subtitle_color
    position = args.position

    if args.text_aware:
        if subtitle_color == "#FFFFFF":
            subtitle_color = "#00E5FF"
        if position == "bottom":
            position = "top"

    try:
        normalize_hex(subtitle_color)
        normalize_hex(args.outline_color)
        normalize_hex(args.onscreen_color)
        normalize_hex(args.onscreen_outline_color)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    onscreen_srt_path = args.onscreen_srt

    if args.extract_onscreen_text_to:
        try:
            ocr_langs = [l.strip() for l in args.ocr_lang.split(",")]
            n = extract_onscreen_text_srt(
                args.video,
                args.extract_onscreen_text_to,
                sample_interval=args.ocr_interval_sec,
                ocr_langs=ocr_langs,
                min_conf=args.ocr_min_conf,
            )
            print(f"[onscreen] OCR extracted {n} segments -> {args.extract_onscreen_text_to}")
            if onscreen_srt_path is None:
                onscreen_srt_path = args.extract_onscreen_text_to
        except RuntimeError as e:
            print(f"Error: {e}")
            sys.exit(1)

    if args.extract_onscreen_text_only:
        print("Done (extract-only)")
        return

    if onscreen_srt_path and not os.path.exists(onscreen_srt_path):
        print(f"Error: onscreen SRT not found: {onscreen_srt_path}")
        sys.exit(1)

    font = args.font or ensure_noto_sans_kr()
    print(
        "Using style: "
        f"font={font}, color={normalize_hex(subtitle_color)}, outline={normalize_hex(args.outline_color)}, "
        f"position={position}, text_aware={args.text_aware}, onscreen_srt={onscreen_srt_path or 'none'}"
    )

    if check_libass():
        print("Using ffmpeg subtitles filter (libass)...")
        if burn_with_ffmpeg(
            args.video,
            args.srt,
            args.output,
            args.fontsize,
            subtitle_color,
            args.outline_color,
            position,
            onscreen_srt=onscreen_srt_path,
            onscreen_fontsize=args.onscreen_fontsize,
            onscreen_color=args.onscreen_color,
            onscreen_outline_color=args.onscreen_outline_color,
            onscreen_position=args.onscreen_position,
        ):
            print(f"Done → {args.output}")
            return
        print("ffmpeg subtitles filter failed, falling back to moviepy...")
    else:
        print("ffmpeg subtitles filter unavailable; using moviepy fallback...")

    print("Using moviepy for subtitle burn-in...")
    try:
        burn_with_moviepy(
            args.video,
            args.srt,
            args.output,
            args.fontsize,
            font,
            subtitle_color,
            args.outline_color,
            position,
            onscreen_srt=onscreen_srt_path,
            onscreen_fontsize=args.onscreen_fontsize,
            onscreen_color=args.onscreen_color,
            onscreen_outline_color=args.onscreen_outline_color,
            onscreen_position=args.onscreen_position,
        )
        print(f"Done → {args.output}")
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
