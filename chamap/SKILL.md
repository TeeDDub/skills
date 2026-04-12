---
name: chamap
description: Use the chamap CLI for directions (car, transit, walking) via T맵 API. Trigger when the user asks for directions, route finding, commute times, transit routes, or walking directions in Korea. Also use for place search, calendar-to-route automation, and Telegram location-based queries.
---

# chamap — T맵 길찾기 CLI

Use the local `chamap` CLI for directions and place search.

## Installation

```bash
# Homebrew
brew tap TeeDDub/tap
brew install chamap

# 또는 Cargo
cargo install --git https://github.com/TeeDDub/chamap-cli
```

## Quick checks

```bash
which chamap
chamap --help
chamap config show
```

If config is missing, ask the user to run:

```bash
chamap config set appKey <T맵-앱키>
```

## Common commands

### Directions

```bash
# 자동차 (기본)
chamap directions "강남역" "판교역"

# 대중교통
chamap directions "강남역" "판교역" --mode transit

# 도보
chamap directions "강남역" "판교역" --mode walk

# 전체 비교
chamap directions "강남역" "판교역" --mode all

# 좌표 입력 (텔레그램 위치 공유)
chamap directions --origin-coords 127.027,37.498 "서울역" --mode transit

# 양쪽 좌표
chamap directions --origin-coords 127.027,37.498 --dest-coords 126.972,37.556

# 상세 경로
chamap directions "강남역" "판교역" --mode car --detail

# JSON 출력
chamap directions "강남역" "판교역" --format json

# 한줄 요약
chamap directions "강남역" "판교역" --mode all --format brief
```

### Search

```bash
chamap search "강남역"
chamap search "판교 카카오"
```

### Alias

```bash
chamap config alias set "집" "127.027,37.498"
chamap config alias set "회사" "126.972,37.556"
chamap config alias list
chamap directions "집" "회사" --mode all
```

## Automation workflows

### 출퇴근 브리핑 (크론)

```bash
chamap directions "집" "회사" --mode all
chamap directions "회사" "집" --mode all
```

### 캘린더 연동

```bash
# gws 스킬로 다음 일정 장소 가져온 뒤
chamap directions "현위치" "<일정장소>" --mode transit
```

### 텔레그램 즉석 질의

사용자가 위치를 공유하면 좌표를 추출하여:

```bash
chamap directions --origin-coords <lon>,<lat> "<목적지>" --mode all
```

## Output format

대중교통은 기본으로 구간별 경로를 보여줌:

```
강남역 → 판교역

🚗 자동차  24분 | 16.0km | 택시 17,900원
🚶 도보  3시간 16분 | 15.3km

🚌 대중교통  22분 | 환승 0회 | 2,650원
  도보 6분 → 강남
  신분당선 → 판교
  도보 1분 → 도착
```

자동차/도보는 `--detail`로 상세 출력.

## Flags reference

| Flag | Description | Default |
|------|-------------|---------|
| `--mode` | `car`, `transit`, `walk`, `all` | `car` |
| `--origin-coords <x,y>` | 출발지 좌표 | - |
| `--dest-coords <x,y>` | 도착지 좌표 | - |
| `--detail` | 상세 경로 출력 | false |
| `--format` | `json`, `text`, `brief` | `text` |
| `--priority` | `recommend`, `time`, `distance` (car만) | `recommend` |

## Security

- API 키는 `~/.config/tmap/config.json`에 저장됨
- API 키를 출력하지 않음
- 변경 작업 전 사용자 확인

## References

For detailed command docs, read files in `references/`.
