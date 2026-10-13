# 매크로 사용 설명서

https://gadget-guide.github.io 에 배포되는 사용 설명서 사이트입니다.

## 구조

- `_src/pages/*.html` — 페이지별 본문 조각 (여기를 고칩니다)
- `_src/style.css`, `_src/manual-assets/` — 공통 스타일과 스크린샷 원본
- `_src/changelog.json` — 업데이트 내역 데이터 (프로그램 저장소의 git 기록에서 생성)
- `build.py` — 위 원본으로 최상단의 `*.html`, `style.css`, `manual-assets/`, `sitemap.xml`, `robots.txt`, `ads.txt` 를 만듭니다

최상단의 생성물은 직접 고치지 말고 `_src/` 를 고친 뒤 다시 빌드하세요.

## 고치는 순서

```bash
python build.py                              # 본문만 고쳤을 때
python build.py --changelog                  # 새 버전을 배포해 업데이트 내역도 갱신할 때
git add -A && git commit -m "..." && git push
```

`--changelog` 는 `.program-repo` 파일(이 PC에만 두고 저장소에는 올리지 않음)에 적힌 프로그램 저장소 경로를 읽습니다.

`main` 브랜치에 푸시하면 GitHub Pages 가 최상단을 그대로 배포합니다. `_src/` 는 밑줄로 시작해서, `build.py` 와 이 파일은 `_config.yml` 의 `exclude` 로 배포에서 빠집니다.

페이지를 추가하려면 `_src/pages/` 에 조각을 만들고 `build.py` 의 `PAGES` 에 한 줄을 넣습니다. 사이트 주소, 문의 연락처, 애드센스 게시자 ID 도 `build.py` 위쪽에서 바꿉니다.
