# chamap search

장소/주소 검색 명령. T맵 POI 통합검색 API 사용.

## Usage

```bash
chamap search <KEYWORD>
```

## Output

```
1. 강남역[2호선] (서울 강남구 역삼동) — 127.027963,37.498046
2. 강남역 1번출구 (서울 강남구 역삼동) — 127.028685,37.498130
3. 강남역[신분당선] (서울 강남구 역삼동) — 127.028324,37.496463
```

최대 5개 결과. 이름, 주소, 좌표(경도,위도) 출력.

## API

- Endpoint: `GET https://apis.openapi.sk.com/tmap/pois`
- 좌표계: WGS84GEO

## Examples

```bash
chamap search "판교역"
chamap search "카카오 판교"
chamap search "서울시 강남구 테헤란로 152"
```
