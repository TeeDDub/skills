# chamap config

설정 관리 명령. 설정 파일: `~/.config/tmap/config.json`

## Commands

### set

```bash
chamap config set <KEY> <VALUE>
```

사용 가능한 키:
- `appKey` — T맵 API 앱키 (필수)
- `mode` — 기본 이동수단 (car/transit/walk/all)
- `format` — 기본 출력 형식 (text/brief/json)
- `priority` — 기본 경로 우선순위 (recommend/time/distance)

### show

```bash
chamap config show
```

현재 설정 JSON 출력.

### alias set

```bash
chamap config alias set <NAME> <LON,LAT>
```

장소 alias 등록. directions에서 장소명 대신 사용 가능.

### alias list

```bash
chamap config alias list
```

### alias remove

```bash
chamap config alias remove <NAME>
```

## Config File Format

```json
{
  "appKey": "your-tmap-app-key",
  "defaults": {
    "mode": "car",
    "format": "text",
    "priority": "recommend"
  },
  "aliases": {
    "집": "127.027,37.498",
    "회사": "126.972,37.556"
  }
}
```

## Examples

```bash
# API 키 설정
chamap config set appKey "hT1YUo..."

# 기본 모드를 대중교통으로 변경
chamap config set mode transit

# 집/회사 등록
chamap config alias set "집" "127.027,37.498"
chamap config alias set "회사" "126.972,37.556"

# 확인
chamap config show
chamap config alias list
```
