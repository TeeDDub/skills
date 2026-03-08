---
name: clip-caption-maker
description: 영상 URL을 받아 다운로드, 구간 자르기, 자막 생성/번역, 요청 시 자막 번인까지 처리한다. Use when user asks to clip/cut a video, make Korean subtitles, or burn subtitles into video.
user-invocable: true
---

# Clip Caption Maker

영상 URL(YouTube/X/Instagram 등 yt-dlp 지원)을 받아 처리한다.

- 기본 출력 폴더: 프로젝트 루트 기준 `_media/{slug}/`
- 번들 스크립트:
  - `{baseDir}/scripts/transcribe.py`
  - `{baseDir}/scripts/burn_subtitles.py`
  - `{baseDir}/scripts/trim_video.py`

## 1) 사용자 의도 확인

1. 사용자 메시지에서 URL을 추출한다.
2. 트리밍 여부를 확인한다: `전체 사용` 또는 `구간 지정(예: 0:30-1:45)` (구간 지정이면 fast/precise 선호 모드 확인, 기본값 fast)
3. 번인 필요 여부, 온스크린 텍스트 번역 필요 여부를 확인한다.

## 2) 영상 다운로드

```bash
python3 -m yt_dlp --print title "{URL}"
```

제목 기반 slug 생성(영문 소문자/숫자/하이픈) 후 다운로드:

```bash
mkdir -p "_media/{slug}"
python3 -m yt_dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
  --merge-output-format mp4 \
  -o "_media/{slug}/original.mp4" \
  "{URL}"
```

길이/해상도 확인:

```bash
ffprobe -v error -show_entries format=duration -show_entries stream=width,height -of csv=p=0 "_media/{slug}/original.mp4"
```

## 3) 트리밍

- 구간 지정인 경우:

```bash
python3 "{baseDir}/scripts/trim_video.py" "_media/{slug}/original.mp4" "_media/{slug}/clip.mp4" \
  --start {start} --end {end} --mode {trim_mode}
```

- fast copy라 컷 포인트가 어긋나면 재인코드 대안:

```bash
python3 "{baseDir}/scripts/trim_video.py" "_media/{slug}/original.mp4" "_media/{slug}/clip.mp4" \
  --start {start} --end {end} --mode precise
```

- 전체 사용인 경우:

```bash
python3 "{baseDir}/scripts/trim_video.py" "_media/{slug}/original.mp4" "_media/{slug}/clip.mp4" --full-copy
```

## 4) 자막 생성 + 한국어 번역

### A) 원본 자막 확인 및 다운로드

```bash
python3 -m yt_dlp --list-subs "{URL}" 2>&1 | head -30
```

자막이 있으면 다운로드:

```bash
python3 -m yt_dlp --write-sub --write-auto-sub --sub-lang "en,ko" --sub-format srt \
  --skip-download -o "_media/{slug}/clip" "{URL}"
```

자막 파일 정규화 (ko 우선, 없으면 en/auto 중 택1):

```bash
mkdir -p "_media/{slug}"
best="$(ls -1 _media/{slug}/clip.ko*.srt 2>/dev/null | head -n1)"
if [ -z "$best" ]; then
  best="$(ls -1 _media/{slug}/clip.en*.srt _media/{slug}/clip.auto*.srt 2>/dev/null | head -n1)"
fi
if [ -n "$best" ]; then
  cp "$best" "_media/{slug}/clip.srt"
fi
```

### B) 자막 파일이 없으면 음성인식으로 생성

```bash
python3 "{baseDir}/scripts/transcribe.py" "_media/{slug}/clip.mp4" "_media/{slug}/clip.srt" --lang auto
```

### C) 한국어 번역

1. `_media/{slug}/clip.srt`를 읽는다.
2. 이미 한국어면 번역을 건너뛴다.
3. 원본을 `_media/{slug}/clip.original.srt`로 백업한다.
4. SRT 구조(번호, 타임스탬프)는 그대로 유지하고 텍스트 라인만 한국어로 번역한다.
5. 번역 결과를 `_media/{slug}/clip.srt`에 덮어쓴다.

## 5) 번인 (요청된 경우만)

기본 번인:

```bash
python3 "{baseDir}/scripts/burn_subtitles.py" \
  "_media/{slug}/clip.mp4" "_media/{slug}/clip.srt" "_media/{slug}/clip-subtitled.mp4"
```

기존 텍스트/자막이 있는 영상(겹침 방지):

```bash
python3 "{baseDir}/scripts/burn_subtitles.py" \
  "_media/{slug}/clip.mp4" "_media/{slug}/clip.srt" "_media/{slug}/clip-subtitled.mp4" \
  --text-aware
```

## 6) 온스크린 텍스트 번역 (요청된 경우만)

### A) OCR 텍스트 후보 추출

```bash
python3 "{baseDir}/scripts/burn_subtitles.py" \
  "_media/{slug}/clip.mp4" "_media/{slug}/clip.srt" "_media/{slug}/clip-subtitled.mp4" \
  --extract-onscreen-text-to "_media/{slug}/onscreen.original.srt" --extract-onscreen-text-only
```

### B) 온스크린 텍스트 번역

1. `_media/{slug}/onscreen.original.srt`를 읽는다.
2. 중요 텍스트만 선별하여 한국어로 번역한다.
   - 워터마크/로고/반복 텍스트는 제거
   - 문맥상 의미 있는 문장/표지/자막성 문구만 유지
   - 번호/타임스탬프 유지, 텍스트만 번역
3. 결과를 `_media/{slug}/onscreen.ko.srt`에 저장한다.

### C) 번역된 온스크린 SRT를 일반 자막과 함께 번인

```bash
python3 "{baseDir}/scripts/burn_subtitles.py" \
  "_media/{slug}/clip.mp4" "_media/{slug}/clip.srt" "_media/{slug}/clip-subtitled.mp4" \
  --text-aware --onscreen-srt "_media/{slug}/onscreen.ko.srt" \
  --onscreen-position top --onscreen-color "#FFD400" --onscreen-outline-color "#000000"
```

## 7) 결과 보고

아래 파일 존재 여부와 SRT 미리보기(앞 5개 블록)를 보고한다:
- `_media/{slug}/original.mp4`
- `_media/{slug}/clip.mp4`
- `_media/{slug}/clip.original.srt` (있을 때)
- `_media/{slug}/clip.srt`
- `_media/{slug}/clip-subtitled.mp4` (번인 시)

에러가 나면 멈추고, 에러 요약 + 다음 선택지(재시도/다른 경로)를 보고한다.

## 의존성

- 필수: `python3`, `ffmpeg`, `yt-dlp`
- 온스크린 OCR: `opencv-python` + `easyocr`
  - 설치: `pip install opencv-python easyocr`
  - 기본 1초 간격 샘플링 + 프레임 diff 변화 감지 → 변화 시점만 OCR → 워터마크 자동 필터링
  - 가사 MV 등 빠른 텍스트 변화: `--ocr-interval-sec 0.3` 권장
  - 긴 영상의 타임아웃 방지: `--ocr-interval-sec 2.0` 권장
