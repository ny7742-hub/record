# 회원 승인제 (2026-09 영업2팀)

`CLAUDE.md`에서 분리한 상세 문서. 내용은 그대로이고 위치만 옮겼다.

- **이메일 로그인 링크(비밀번호 없음) → 이름 입력(승인 대기) → 관리자 [승인] → 사용**, 나중에 관리자가 [삭제]하면 그 사람은 즉시 닫힌다.
  (처음엔 Google 로그인이었으나 2026-09 영업2팀 요청으로 이메일 방식으로 바꿨다.)
  **이메일만 적고 바로 들어가게 하면 안 된다** — 팀원 이메일을 아는 사람이면 누구나 그 사람으로 들어온다.
  그래서 `sendSignInLinkToEmail`로 메일함에 링크를 보내고(`authSendLink`), 링크로 돌아오면 `_authCompleteLink`가 로그인한다.
  보낸 이메일은 `localStorage.authEmailForSignIn`에 두고, 다른 브라우저에서 링크를 열면 이메일을 한 번 더 묻는다.
  링크 처리 중에는 `_authLinkPending`으로 로그아웃 콜백이 화면을 덮어쓰지 못하게 막는다(안 막으면 이메일 재입력 화면이 사라진다).
  로그인 후 주소창의 일회용 코드(`oobCode`)는 `history.replaceState`로 지운다.
  헤더 오른쪽 `authChip`에 이름·로그아웃, 관리자면 `👥 사용자 관리`(대기 인원 표시).
- **화면 게이트만으로는 막히지 않는다** — 페이지 코드에 DB 주소가 있어 누구나 REST로 `ws/` 전체(`quickCreds` 포함)를 읽을 수 있었다.
  실제 잠금은 저장소의 **`database.rules.json`** 을 Firebase 콘솔 Realtime Database → 규칙에 붙여넣어야 한다.
  규칙: `ws/`는 `access/members/{uid}`가 있는 사람만 읽기·쓰기, `access/pending/{uid}`는 본인만 요청, 승인·삭제는 `access/admins`만.
- **켜지는 시점**: `access/meta/bootstrapped`가 생긴 뒤부터 게이트가 뜬다(`_authGateOn`). 그 전엔 예전처럼 쓰고
  헤더에 `🔐 회원 승인제 시작` 버튼만 있다 — Google 로그인을 콘솔에서 켜기 전에 게이트부터 뜨면 팀 전체가 못 들어오기 때문.
  규칙을 잠근 뒤에는 로그인 전 `bootstrapped` 읽기가 거부되는데 그것도 켜짐으로 본다.
  첫 관리자는 `bootstrapped`가 없을 때 한 번만 스스로 등록할 수 있다(`authBootstrap`, 규칙도 같은 조건).
- **리스너(`fbListen`)는 승인 뒤에 붙인다** — 규칙이 잠긴 상태에서 로그인 전에 `.on()`을 걸면 거부되어 그대로 끊긴다.
  `wsSetItem`도 `_authState`가 `member`(또는 설정 전 `open`)일 때만 Firebase에 쓴다.
- 사용 중 삭제되면 `FB_PATH`에 해당하는 localStorage 팀 자료를 지우고 새로고침한다.
- 로컬(localhost)은 게이트 없이 열리고, `?gate=1`로 확인할 수 있다(로그인 화면의 `로컬 개발: 로그인 없이 계속`).
- **도입 순서**(콘솔 작업이라 사람이 해야 함): ① Authentication → 로그인 방법 → **이메일/비밀번호** 추가 → **이메일 링크(비밀번호가 없는 로그인)** 켜기
  ② 승인된 도메인에 `ny7742-hub.github.io` ③ 배포 사이트에서 `🔐 회원 승인제 시작` → 메일 링크로 로그인 → `👑 첫 관리자로 등록` ④ 팀원 승인 요청·승인
  ⑤ **`database.rules.json` 붙여넣고 게시** ⑥ `quickCreds`에 있던 사이트 비밀번호 교체(그동안 공개 상태였음).
