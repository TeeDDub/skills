# chamap directions

길찾기 명령.

## Usage

```bash
chamap directions [ORIGIN] [DESTINATION] [FLAGS]
```

ORIGIN과 DESTINATION은 장소명, 주소, 또는 등록된 alias. `--origin-coords` / `--dest-coords`로 좌표를 직접 지정하면 생략 가능.

## Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--mode` | string | `car` | 이동수단: `car`, `transit`, `walk`, `all` |
| `--origin-coords` | string | - | 출발지 좌표 `경도,위도` |
| `--dest-coords` | string | - | 도착지 좌표 `경도,위도` |
| `--detail` | bool | false | 상세 턴바이턴 출력 |
| `--format` | string | `text` | 출력 형식: `text`, `brief`, `json` |
| `--priority` | string | `recommend` | 경로 우선순위 (car만): `recommend`, `time`, `distance` |

## Input Resolution Order

1. `--origin-coords` / `--dest-coords` → 좌표 직접 사용
2. alias 매칭 → `~/.config/tmap/config.json`의 aliases
3. T맵 POI 검색 → 키워드로 지오코딩

## Output Modes

### text (기본)

자동차/도보는 한줄 요약, 대중교통은 구간별 경로 포함.

### brief

모든 모드를 한줄로: `자동차 24분(16.0km), 대중교통 22분(환승0회), 도보 3시간16분`

### detail

모든 구간의 턴바이턴 안내.

### json

API 응답을 가공한 JSON. Route 객체 배열.

## API Endpoints

| Mode | Method | Endpoint |
|------|--------|----------|
| car | POST | `/tmap/routes?version=1` |
| transit | POST | `/transit/routes` |
| walk | POST | `/tmap/routes/pedestrian?version=1` |

Base URL: `https://apis.openapi.sk.com`

## Examples

```bash
# 기본 자동차
chamap directions "서울역" "인천공항"

# 대중교통 상세
chamap directions "강남역" "홍대입구역" --mode transit

# 좌표 → 장소명
chamap directions --origin-coords 127.0,37.5 "강남역" --mode all

# alias 사용
chamap directions "집" "회사" --mode all --format brief

# JSON 파이프
chamap directions "강남역" "판교역" --mode car --format json | jq '.[] .duration_s'
```
