# clip-caption-maker

영상 URL을 받아 다운로드, 구간 자르기, 자막 생성/번역, 자막 번인까지 처리하는 AI 에이전트 스킬.

## 기능

- YouTube/X/Instagram 등 yt-dlp 지원 URL에서 영상 다운로드
- 구간 트리밍 (fast copy / precise 재인코딩)
- 음성인식 자막 생성 (mlx-whisper)
- 자막 한국어 번역
- 자막 번인 (하드코딩)
- 온스크린 텍스트 OCR + 번역 + 번인

## 설치

### Claude Code

```bash
# 프로젝트 스킬로 설치 (현재 프로젝트에서만 사용)
mkdir -p .claude/skills
cp -r clip-caption-maker .claude/skills/

# 또는 개인 스킬로 설치 (모든 프로젝트에서 사용)
cp -r clip-caption-maker ~/.claude/skills/
```

설치 후 `/clip-caption-maker` 슬래시 커맨드로 호출할 수 있다.

### OpenClaw

```bash
cp -r clip-caption-maker ~/.openclaw/workspace/skills/
```

## 사전 요구사항

### 필수

```bash
brew install ffmpeg yt-dlp
```

### 음성인식 (transcribe.py)

```bash
pip install mlx-whisper
```

### 온스크린 OCR (선택)

```bash
pip install opencv-python easyocr
```

## 사용 예시

```
/clip-caption-maker https://youtu.be/example
```

에이전트가 트리밍 여부, 번인 필요 여부 등을 물어본 뒤 자동으로 처리한다.
