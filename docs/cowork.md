# 코스트코 상품개발 협업 (`cowork.html`, 2026-09)

디자인팀 · 생산팀 · 웹디자인팀 · 영업2팀이 **코스트코 상품 하나를 같이 보며 디자인·일정을 체크**하는 별도 페이지.

- 파일: `cowork.html` (자비스 `index.html`과 분리된 단일 파일)
- 주소: https://ny7742-hub.github.io/record/cowork.html
- 외부 라이브러리 없음 (Firebase SDK 8.10.1만)

## 왜 별도 페이지인가
자비스(`index.html`)의 팀원 승인(`access/members`)은 **`ws/` 전체 — 매출·마진·원가까지** 열어준다.
타팀을 거기 넣으면 영업 데이터가 통째로 보인다. 그래서

- 데이터는 `cowork/` 아래에만 쓰고,
- 접근 권한 목록을 `access/cowork/{uid}`로 따로 둔다.

**`access/cowork`에 승인된 사람은 이 페이지만 쓴다.** 자비스 팀원(`access/members`)은 따로 승인하지 않아도 이 페이지를 쓸 수 있다(규칙에서 OR).
승인·삭제는 자비스 관리자(`access/admins`)가 이 페이지의 `👥 사용자 관리`에서 한다.

## 로그인
자비스와 **같은 이메일 링크 방식**(비밀번호 없음)이고 승인 목록만 다르다. 흐름·주의점은 [`auth.md`](auth.md)와 동일:
이메일 입력 → 메일함 링크 → 이름 + **소속 팀** 선택 → 승인 대기 → 관리자 승인 → 사용.

- 대기 경로는 `access/coworkPending/{uid}`, 승인되면 `access/cowork/{uid}={name,team,email,at,by}`.
- 게이트가 켜지는 시점도 자비스와 같다 — `access/meta/bootstrapped`가 있어야 뜬다. 그 전에는 누구나 쓰는 열린 상태.
- 로그인 여부는 `access/cowork/{uid}`와 `access/members/{uid}` **두 곳을 동시에** 본다(`authCheck`).
  둘 다 확인될 때까지 화면을 넘기지 않는다(`settle`) — 한 쪽만 보고 판단하면 자비스 팀원이 승인 요청 화면으로 튕긴다.
- **로컬(file·localhost)에서는 저장되지 않는다**(`canWrite`가 false, `needWrite`가 안내). 자비스와 같은 방침 — 테스트가 팀 보드를 더럽히지 않게.

## 데이터 구조 (`cowork/`)
```
cowork/items/{id}     = {id,name,item(코스트코 아이템번호),season,owner,due,memo,state,cnt,
                         steps:{단계키:{state,due,doneAt,byName,memo}}, imgs:[{id,t,by,at}], links:[{u,t,by,at}]}
cowork/files/{fid}    = "data:image/jpeg;base64,..."   ← 목록에선 안 읽는다
cowork/comments/{itemId}/{cid} = {n(이름),t(팀),x(본문),at,uid}
cowork/stepdef        = [{k,n,t}]  공통 진행 단계
cowork/log            = 최근 활동 (limitToLast 120)
```

- `state`: `active` · `hold` · `done`(모든 단계 완료 시 자동) · `drop`
- 단계 `state`: `todo → doing → done → hold` (동그라미 버튼을 누를 때마다 순환)
- **이미지는 카드를 열 때만 읽는다** — `cowork/files`는 리스너를 걸지 않고 `once`로 가져와 `_imgCache`에 담는다.
  전체를 구독하면 보드가 base64 수십 장을 들고 무거워진다.
- 업로드는 캔버스로 **긴 변 1000px · JPEG 0.72**로 줄여 넣는다(900KB 넘으면 0.55로 한 번 더). 링크(드라이브·캔바)도 같이 붙일 수 있다.
- **여러 장을 한꺼번에 올릴 때는 `imgs`에 트랜잭션으로 이어 붙인다** — `set`으로 하면 서로의 목록을 덮어쓴다.
- Firebase는 중간이 빈 배열을 객체로 돌려주므로 `imgs`·`links`는 항상 `toArr()`로 받는다.

## 기본 9단계 (`DEFAULT_STEPS`)
① 기획·제안(영업2) ② 디자인 시안(디자인) ③ 시안 확정·코스트코 컨펌(영업2) ④ 샘플 제작(생산) ⑤ 샘플 승인(영업2)
⑥ 패키지·라벨 디자인(웹디자인) ⑦ 패키지 인쇄(생산) ⑧ 본생산(생산) ⑨ 입고·납품(영업2)

헤더 `🧭 단계 설정`에서 이름·담당팀·순서를 팀이 직접 고치고 추가/삭제할 수 있다(`cowork/stepdef`, 팀 전체 공통).
단계를 지워도 상품에 남은 그 단계 기록은 지우지 않고 화면에서만 빠진다.

## 화면
- **상품 보드** — 카드마다 단계 도트 9개(완료 초록 · 진행 주황 · 보류 회색 · 지연 빨강 테두리), 지금 차례인 단계와 담당팀, 가장 가까운 마감 D-day, 코멘트 수, 시안 썸네일.
  필터: 검색 · 팀(`우리 팀 차례`는 현재 단계 담당이 내 팀인 것만) · 상태 · 정렬.
- **일정** — 12주 주간 간트. 행=상품, 칸=그 주에 걸린 단계 마감(색=담당팀, 완료는 흐리게, 지연은 빨간 테두리), `🎯 납품`은 목표 납품일. `← 4주 전 / 이번 주 / 4주 후 →`.
- **우리 팀 할 일** — 내 팀이 담당인 미완료 단계를 `마감 지남 / 7일 내 / 8~30일 / 그 이후·미정`으로 묶는다. 여기서 바로 상태·마감일을 고친다. **보류 상품은 빠진다.**
- **최근 활동** — 누가 무엇을 바꿨는지(`cowork/log`). 단계 완료, 마감일 변경, 코멘트, 이미지 업로드 등.
- 상세 창은 다른 사람이 고치면 따라 바뀌는데, **내가 입력 중이면 다시 그리지 않는다**(`refreshDet` — 안 막으면 타이핑이 날아간다).

## 도입 순서 (콘솔 작업은 사람이 해야 함)
1. `database.rules.json`을 Firebase 콘솔 → Realtime Database → 규칙에 **붙여넣고 게시** (`cowork`·`access/cowork`·`access/coworkPending` 항목이 추가됐다)
2. 자비스에서 회원 승인제를 켠 상태여야 게이트가 뜬다(`access/meta/bootstrapped`) — [`auth.md`](auth.md) 참고
3. 타팀에게 https://ny7742-hub.github.io/record/cowork.html 안내 → 각자 이메일 링크로 로그인 → 이름·소속 팀 적어 승인 요청
4. 관리자가 `👥 사용자 관리`에서 승인

## 주의
- 팀 목록(`TEAMS`)은 코드 상수다. 팀이 늘면 `TEAMS`에 추가해야 한다(색도 같이).
- 자비스 팀원이 이 페이지에서 `팀 변경`을 하면 `access/cowork` 기록이 없어 `localStorage.coworkMyTeam`에만 남는다(그 브라우저 한정).
- 이미지는 Realtime Database에 base64로 들어간다. 장수가 많이 쌓이면 Storage로 옮기는 걸 검토할 것.
