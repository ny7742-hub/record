# AGENTS.md — Codex(ChatGPT)용 안내

이 저장소는 평소 Claude Code로 작업한다. Claude 사용량이 다 떨어졌을 때 Codex(ChatGPT)로 이어서 작업하려고 둔 파일이다.

## 먼저 읽을 것
- **`CLAUDE.md`를 먼저 끝까지 읽는다.** 프로젝트 설명·구조·주의사항·배포 방법이 모두 거기 있다. 이 파일에는 다시 적지 않는다.
- 기능별 상세는 `CLAUDE.md`의 "상세 문서" 목록(`docs/*.md`)에 있다. 고칠 기능의 문서만 연다.
- `index.html`은 1.9MB라 통째로 읽지 말고 검색(`rg`)으로 찾은 뒤 필요한 부분만 읽는다.

## 이어받기
- 시작할 때 `git status`와 `git diff`로 Claude가 하다 만 변경이 있는지 본다. 있으면 무엇을 하던 중인지 사용자에게 먼저 확인한다.
- 최근 작업 흐름은 `git log --oneline -20`으로 본다.

## 작업 규칙
- 설명·진행 보고·마무리 답은 모두 **한글**로 한다.
- 코드를 고친 뒤에는 커밋하고 `git push`까지 한다(GitHub Pages 자동 반영).
- 여러 세션이 `index.html`을 동시에 고친다. **커밋 전에 `git diff`로 내가 바꾼 부분만 있는지 확인**하고, 내 변경만 `git add`한다(`git add -A`·`git add .` 금지).
- "검수/검증해 달라"는 요청이면 문제를 찾아도 고치지 말고 보고만 한다.
- 외부 시스템(wsstudio, PlayMD 등)의 숫자는 그 화면의 묶음·우선순위 규칙을 소스에서 확인하고, 전 품목을 대조한 뒤 보고한다.
- JS 문법 오류가 나면 앱 전체가 멈춘다. 고친 뒤 문법을 꼭 확인한다.
- 기능을 고치면 `docs/`의 해당 문서도 같이 고친다.

## 한글 깨짐 주의 (Windows PowerShell 5.1)
- 파일은 모두 UTF-8(BOM 없음)이다. PowerShell에서 읽을 때는 **`Get-Content -Encoding UTF8`** 을 붙인다(안 붙이면 한글이 깨져 보인다).
- 파일 수정은 `apply_patch`로 한다. `Set-Content`·`Out-File`·`>`로 파일을 쓰지 않는다 — 인코딩이 바뀌어 `index.html`의 한글이 통째로 깨진다.
