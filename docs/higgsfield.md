# 🎨 힉스필드 탭 — 코스트코 RRP 디자인 시안 모음

2026-10-22 영업2팀. 코스트코 RRP(진열 박스) 디자인을 힉스필드(higgsfield.ai, AI 이미지·영상 생성)에서 만들고,
나온 시안을 자비스에 모아 팀이 같이 본다. 탭 버튼은 `💡 코스트코 제안상품` 다음(`tab-higgs` / `page-higgs`, `renderHiggs`).

## 힉스필드는 새 창으로
- 힉스필드는 `X-Frame-Options: SAMEORIGIN`과 CSP `frame-ancestors`(자기 도메인만)로 **iframe 끼워 넣기를 막는다** — 자비스 안에 화면을 넣을 수 없다.
- 그래서 `↗ 힉스필드 열기`(`hgOpenSite`)가 새 창으로 연다. 로그인·크레딧은 각자 힉스필드 계정.

## 시안 모음
- 올리기: 칸을 눌러 파일 고르기 · 파일을 화면에 끌어 놓기 · 이 탭이 열려 있을 때 **Ctrl+V**(힉스필드에서 이미지 복사 → 붙여넣기). 여러 장 한꺼번에 된다.
- 이미지는 긴 변 1600px JPEG로 줄인다(`_hgShrink`, 1.2MB 넘으면 화질 낮춤, 투명 배경은 흰색). 파일 이름이 제목 기본값.
- 시안마다: 제목 · 메모/프롬프트 · `☆ 채택`(채택은 주황 테두리, 위 `⭐ 채택만`으로 거르기) · `⬇` 받기 · `🗑` 삭제(팀 전체에서 지워짐) · 이미지 누르면 크게 보기.
- 최신 올린 것이 앞. 올린 사람(`by`)·시각·크기를 카드 아래에 보인다.

## 저장 (팀 공유)
- `ws/hgRrp/items/{id}` = `{t 제목, memo, pick, by, at, w, h}` — 시안마다 따로 써서(`_hgPut`, `fbDB.ref().update`) 동시에 올려도 서로 덮지 않는다.
- `ws/hgRrp/files/{id}` = 이미지 dataURL. **목록만 `fbListen`이 듣고**, 이미지는 탭을 그릴 때 한 장씩 `once`로 받는다(`_hgLoadImg`, 캐시 `_hgImg`) —
  다른 탭만 쓰는 사람은 이미지를 받지 않는다.
- 제목·메모를 고치면 리스너가 다시 그리는데, 쓰던 칸의 포커스·커서를 되살린다(`data-hg`).
- 로컬 실행(`WS_LOCAL_ONLY`)은 팀 공유에 안 쓰므로 이 브라우저 localStorage(`hgRrpItems`·`hgRrpFiles`)에만 두고, 리스너도 덮어쓰지 않는다.

## ✨ 힉스필드로 만들기 (자동화 PC가 API로)
- 문구(필수) + 참고 이미지(선택)를 넣고 `✨ 만들기` → 1~3분 뒤 결과가 **시안 모음에 바로** 들어온다(카드에 `✨ 모델 이름`, 메모 = 문구).
  참고 이미지는 `＋ 참고 이미지`, 만들기 칸에 커서를 두고 Ctrl+V, 또는 시안 카드의 `➕ 참고로`(만든 결과를 다시 고치기).
- 모델: **Grok Image 2.0**(`xai/grok-imagine-image-2.0`, 문구만 또는 참고 0~10장, 비율 자동 가능) · **Qwen Image 3 편집**(`alibaba/qwen-image-3/edit`, 참고 1~3장 필수).
  비율 · 해상도 1K/2K. 한 번에 1장. 크레딧은 성공한 것만 쓰인다(실패·nsfw는 환불).
- **브라우저에서 API를 못 부른다** — `api.higgsfield.ai`가 다른 사이트 요청(CORS)을 허용하지 않고, 키를 페이지에 둘 수도 없다.
  그래서 자비스는 요청만 남기고 자동화 PC가 처리한다(네이버 최저가와 같은 방식):
  - `ws/hgGen/{id}` = `{state 요청→처리중→완료/실패, prompt, model, ar, res, by, at, nref, hs(힉스필드 상태), out(만든 시안 id), error}` — 최근 8건을 만들기 칸 아래에 보인다(실패는 `다시 넣기`).
  - `ws/hgGenRef/{id}/{i}` = 참고 이미지(JPEG dataURL, 먼저 쓰고 요청을 남긴다) — 처리 끝나면 지운다.
  - `ws/hgGenWatch` = `{at, key}` 1분마다 — 만들기 칸 제목 옆에 `🟢 자동화 PC 켜짐 · API 키 있음/없음`.
  - 로컬 실행에서는 요청을 보내지 않는다(팀 공유 꺼짐).
- 자동화 PC: `automation/higgs-gen.mjs`(`higgsTick`)를 `saip-watch.mjs`가 5초마다(밤 15초) 따로 돌린다. 참고 이미지 → `files/generate-upload-url` → PUT →
  모델 요청(Idempotency-Key = 요청 id) → `requests/{id}/status` 4초마다(최대 8분) → 결과를 받아 `ws/hgRrp/items·files`에 넣는다
  (6MB 넘으면 파일 대신 힉스필드 주소 `u`만, 보관 7일 이상). 15분 넘게 `처리중`이면 실패로 바꾼다. 기록은 최근 40건.
  `jarvis-rest.mjs`의 `wsRaw`(객체 그대로 읽고 쓰기)를 쓴다.
- **API 키는 자동화 PC의 `automation/higgsfield-api.json`에만** `{"keyId":"…","keySecret":"…"}`(cloud.higgsfield.ai에서 만든 키) — 자비스·팀 공유·로그에 남기지 말 것.
  `node higgs-gen.mjs --check`로 키만 확인(크레딧 안 씀), `--once`로 한 번 처리.

## 참고
- 기존 RRP 패키지 시안(에이린, PANTONE 657C `#C8D8EB` · 7686C `#1D4F91`)은 3D 집기 탭 `코스트코 팔레트 (RRP 에이린)`의 `RRP_SRC`에 있다.
