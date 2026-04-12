# chamap

T맵 API 기반 길찾기를 Claude Code에서 바로 사용하는 AI 에이전트 스킬. 자동차, 대중교통, 도보 경로를 터미널에서 확인하고, 텔레그램 위치 공유나 캘린더 연동 등 자동화 워크플로우를 지원한다.

## 기능

- 자동차 / 대중교통 / 도보 길찾기
- 전체 이동수단 비교 (`--mode all`)
- 대중교통 구간별 상세 경로 (노선, 정거장, 환승)
- 좌표 직접 입력 (텔레그램 위치 공유 연동)
- 장소 alias 등록 (집, 회사 등)
- 출퇴근 브리핑, 캘린더 연동 자동화

## 설치

### Claude Code

```bash
# 프로젝트 스킬로 설치 (현재 프로젝트에서만 사용)
mkdir -p .claude/skills
cp -r chamap .claude/skills/

# 또는 개인 스킬로 설치 (모든 프로젝트에서 사용)
cp -r chamap ~/.claude/skills/
```

설치 후 길찾기 관련 질문을 하면 자동으로 트리거된다.

### OpenClaw

```bash
cp -r chamap ~/.openclaw/workspace/skills/
```

## 사전 요구사항

### chamap CLI 설치

```bash
# Homebrew (추천)
brew tap TeeDDub/tap
brew install chamap

# 또는 Cargo
cargo install --git https://github.com/TeeDDub/chamap-cli
```

### 인증

[T맵 API 발급 가이드](https://transit.tmapmobility.com/guide/procedure)를 참고하여 앱키를 발급받은 뒤:

```bash
chamap config set appKey <앱키>
```

### 장소 등록 (선택)

```bash
chamap config alias set "집" "127.027,37.498"
chamap config alias set "회사" "126.972,37.556"
```

## 사용 예시

```
강남역에서 판교역까지 어떻게 가?
집에서 회사까지 대중교통으로 얼마나 걸려?
[위치 공유] 서울역까지 길찾기 해줘
내일 첫 일정 장소까지 이동 시간 알려줘
```
