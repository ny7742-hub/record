# 💬 하이 자비스 (채팅)

2026-10-22 영업2팀 "자비스 안에 채팅으로 문의할 수 있는 하이 자비스 — 클로드에 문의하는 것처럼, 탭을 이동할 때마다 항상 같은 자리".

## 화면 (index.html 맨 끝, `</body>` 바로 앞 블록)
- `#jvcBtn` **오른쪽 위** 검은색 큰 `💬 하이 자비스` 단추(2026-10-22 영업2팀 "오른쪽 상단으로, 2배 크기, 블랙") · `#jvcPanel` 채팅창은 단추 바로 아래(머리도 검은색).
  둘 다 탭(`page-*`) 밖 `position:fixed`라 **어느 탭이든 같은 자리**. `body{zoom:1.12}` 때문에 높이는 `vh / 1.12`로 잡는다.
- 단추가 헤더 오른쪽 이름·사용자 관리·로그아웃 칩(`#authChip`)을 가리지 않게, 단추가 보일 때 body에 `jvc-on`을 달아 칩을 왼쪽으로 250px 비킨다.
  모바일(≤700px)은 단추를 작게(14px) 하고 제목 오른쪽을 비워 칩이 둘째 줄로 내려가게 한다 · 채팅창은 좌우 8px, 단추 아래부터 화면 끝까지.
- 승인된 사용자(`_authState==="member"`)만 단추가 보인다(게이트 `#authGate` z-index 100000 아래, 채팅 9990~9991).
- 대화·열림 상태·"화면 내용 같이 보내기"는 **이 브라우저 localStorage**(`jvcLog` 최근 60개 · `jvcOpen` · `jvcOpt`). 새 대화 = 지우기.
- Enter 보내기 · Shift+Enter 줄바꿈 · 답하는 중 `■`로 멈추기 · 답마다 `⧉ 복사`. 답은 마크다운(굵게·목록·표·코드·링크)을 간단히 그린다(`md()`).
- "지금 화면 내용 같이 보내기"(기본 켬): 보이는 `page-*`의 `innerText` 8천 자까지 + 탭 이름을 질문에 붙인다 — "이 표 요약해 줘" 같은 질문용.
- 단추의 점: 초록 = 자동화 PC 켜짐(ws/jvChatAlive 3분 안), 빨강 = 꺼짐. 창 아래 `● 연결됨 / 자동화 PC 꺼짐 / API 키 필요`.

## 흐름
1. 화면이 `ws/jvChat/{id}`에 `{uid, by, at, tab, screen, msgs:[{r:'u'|'a', t}](최근 20개), state:'요청'}`를 쓰고 그 칸을 듣는다(`on('value')`).
2. 자동화 PC `automation/saip-watch.mjs`가 2초마다(밤 21~7시 6초) `jarvis-chat.mjs`의 `chatTick()`을 부른다 → `'답하는중'`으로 바꾸고 **화면 글자(screen)는 바로 지운다**.
3. Claude API(스트리밍)로 답을 만들며 0.6초마다 `ans`(지금까지 답)·`st`(웹 검색 중… 같은 진행 문구)를 고쳐 쓴다 → 화면이 실시간으로 이어 그린다.
4. 끝나면 `'완료'`(또는 `'실패'` + `err`). 멈추기는 화면이 `state:'중지'` → chatTick이 스트림을 끊는다.
5. 끝난 칸은 30분 뒤 지운다. 10분 넘게 아무도 안 가져간 요청은 '실패'로. 동시에 3개까지.

## 자동화 PC (`automation/jarvis-chat.mjs`)
- **API 키는 자동화 PC의 `automation/anthropic-api.json`에만**: `{"apiKey":"sk-ant-…", "model":"claude-opus-5-5", "effort":"medium"}` (model·effort 생략 가능).
  키는 console.anthropic.com → API Keys에서 만든다(클로드 앱 구독과 별도, 쓴 만큼 과금). 자비스(공개 페이지)·팀 공유 자료·로그에 남기지 말 것.
  키가 없으면 질문에 "자동화 PC에 Claude API 키가 아직 없습니다"로 답한다(`ws/jvChatAlive.key=false`).
- 시험: `node jarvis-chat.mjs --q="질문"` — 팀 공유에 쓰지 않고 화면에만 답을 찍는다.
- Claude가 쓰는 것: 시스템 프롬프트(역할·규칙 + 저장소 `CLAUDE.md` 전문, 캐시) · `read_jarvis_doc` 도구(이 `docs/*.md`를 필요할 때 읽음) · 웹 검색(질문당 3번까지) · 마지막 질문에 붙인 날짜·묻는 사람·탭·화면 글자.
  **자비스를 대신 누르거나 팀 자료를 고치지는 않는다** — 답만 한다.
- 모델 기본 `claude-opus-5-5`(effort medium, adaptive thinking) + 서버 폴백(`server-side-fallback-2026-07-01`, `fallbacks:'default'`).
  첫 요청이 400(형식 거절)이면 베타·웹 검색 없이 한 번 더 한다(모델을 바꿔 적었을 때 등).
- 고친 뒤 반영: `automation/logs/saip-watch.restart` 파일을 만들면 watcher가 돌고 있는 작업이 끝난 뒤 스스로 다시 뜬다.
- 같은 오류는 saip-watch 로그에 5분에 한 번만 적는다. 답 하나마다 `💬 하이 자비스 (이름) N초 · 답 N자`.

## 주의
- `ws/jvChat`은 팀 공유라 승인된 팀원은 서로의 질문을 읽을 수 있다(30분 뒤 지워짐). 민감한 내용은 묻지 않도록 안내.
- 설명서(`docs/*.md`)를 고치면 하이 자비스의 답도 바로 바뀐다(자동화 PC가 저장소 폴더 `../화이트샌즈 바코드 검색기`에서 읽는다 — 그 PC 저장소가 최신이어야 한다).
