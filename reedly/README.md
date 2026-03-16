# reedly

Feedly RSS 피드를 Claude Code에서 바로 읽고, 검색하고, 요약하는 AI 에이전트 스킬.

## 기능

- 미읽은 기사 수 확인
- 카테고리/피드별 기사 읽기
- 기사 요약 또는 원문 보기
- 피드 및 기사 검색
- 저장된 기사(하이라이트) 확인

## 설치

### Claude Code

```bash
# 프로젝트 스킬로 설치 (현재 프로젝트에서만 사용)
mkdir -p .claude/skills
cp -r reedly .claude/skills/

# 또는 개인 스킬로 설치 (모든 프로젝트에서 사용)
cp -r reedly ~/.claude/skills/
```

설치 후 피드 관련 질문을 하면 자동으로 트리거된다.

### OpenClaw

```bash
cp -r reedly ~/.openclaw/workspace/skills/
```

## 사전 요구사항

### reedly CLI 설치

```bash
# Homebrew (추천)
brew tap TeeDDub/tap
brew install reedly

# 또는 uv
uv tool install git+https://github.com/TeeDDub/reedly.git

# 또는 pip
pip install git+https://github.com/TeeDDub/reedly.git
```

### 인증

```bash
reedly login
```

[Feedly Developer Access Token](https://feedly.com/v3/auth/dev)을 입력한다.

## 사용 예시

```
뉴스 뭐 있어?
Tech 카테고리 최신 기사 5개 요약해줘
AI 관련 기사 검색해줘
Comics 기사 3개 전체 내용 보여줘
```
