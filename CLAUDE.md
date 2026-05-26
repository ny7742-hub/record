# 화이트샌즈 판매일보 웹앱

## 프로젝트 개요
화이트샌즈 매장 판매일보 등록용 단일 HTML 웹앱.

- **파일**: `index.html` 단일 파일
- **GitHub**: https://github.com/ny7742-hub/record
- **배포 URL**: https://ny7742-hub.github.io/record/
- **외부 라이브러리**: SheetJS CDN (`xlsx.full.min.js` v0.18.5)

## 현재 기능
- 상품명 + 칼라 통합 검색 (실시간)
- 칼라 칩 자동 표시 및 선택
- 키보드 방향키로 검색결과 탐색, Enter로 추가
- 선택 목록 최신순 정렬, 중복 추가 허용
- 종류별/전체 할인율 일괄 적용
- 판매 양식 엑셀 다운로드 (시트명: 매장판매양식)
- 상품 데이터 업데이트 기능 (xlsx 업로드 → localStorage 저장)
- 매장코드 자동변환: 센텀→LSC, 동부산→LDB, 평촌→LPC, 김포→LKP

## 배포 방법
```powershell
git add index.html
git commit -m "수정 내용"
git push
```
push하면 GitHub Pages에 자동 반영됨 (1~2분 소요).

## 주의사항
- JS 수정 시 문법 오류에 주의 (오류 시 검색 자체가 안 됨)
- `index.html`이 647KB로 크므로 Read 시 offset/limit 분할 필요
