"""매크로 사용 설명서 사이트 생성기.

_src/pages/*.html(본문 조각) + _src/style.css + _src/manual-assets/ 를 읽어
저장소 최상단에 완성된 정적 사이트를 만든다. GitHub Pages 가 최상단을 그대로 배포하고,
밑줄로 시작하는 _src/ 는 배포에서 빠진다.

    python build.py                          # 사이트 다시 만들기
    python build.py --changelog              # 업데이트 내역도 프로그램 저장소의 git 기록에서 새로 뽑기

페이지를 추가하려면 _src/pages/ 에 본문 조각을 만들고 아래 PAGES 에 한 줄을 넣는다.
최상단의 *.html, style.css, manual-assets/ 는 생성물이니 직접 고치지 않는다.
"""
import argparse
import html
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "_src"
OUT = ROOT

# 호스팅 주소가 바뀌면 여기만 고친다(canonical, sitemap, robots 에 쓰인다).
SITE_URL = "https://gadget-guide.github.io"
SITE_NAME = "매크로 사용 설명서"
ADSENSE_CLIENT = "ca-pub-9181621892668352"
# 구글 서치 콘솔 소유권 확인 값
GOOGLE_SITE_VERIFICATION = "LOSXsZBOLtsS_0UJziLJOx76pGKAXK6D4Hu864cuCBM"
# 소개·문의 페이지에 공개할 연락처(HTML). 비워두면 "관리자에게 문의" 안내만 나온다.
CONTACT_HTML = ""

# (파일명, 메뉴 묶음, 메뉴에 보이는 이름, <title>, 검색 결과 설명, 마지막 수정일)
PAGES = [
    ("index", "home", "홈", SITE_NAME,
     "매크로의 설치, 휴대폰 연결(USB 디버깅), 기능별 사용법, 무인 자동 실행, 문제 해결을 정리한 공식 사용 설명서입니다.",
     "2026-10-13"),
    ("manual-start", "manual", "시작하기 전에", "1. 시작하기 전에",
     "매크로가 제공하는 다섯 가지 기능과 기능별 준비물, 설명서를 읽는 순서를 안내합니다.",
     "2026-10-13"),
    ("manual-install", "manual", "설치와 첫 실행", "2. 설치와 첫 실행",
     "압축 풀기부터 실행 암호 입력, Windows 보호 경고 대처, 자동 업데이트까지 설치 과정을 순서대로 설명합니다.",
     "2026-10-13"),
    ("manual-layout", "manual", "화면 구성 한눈에 보기", "3. 화면 구성 한눈에 보기",
     "사이드바, 계정 관리, 옵션, 시작/정지 버튼, 로그창 등 프로그램 화면의 각 영역을 설명합니다.",
     "2026-10-13"),
    ("manual-account", "manual", "계정 등록하기", "4. 계정 등록하기",
     "기능별 계정 등록 방법과 사용/출석 체크박스의 의미, 계정 정보가 저장되는 위치를 설명합니다.",
     "2026-10-13"),
    ("manual-adb", "manual", "안드로이드 앱 매크로 연결하기", "5. 안드로이드 앱 매크로 연결하기 (USB 디버깅)",
     "개발자 모드와 USB 디버깅을 켜고 PC와 휴대폰을 연결하는 과정을 사진과 함께 단계별로 설명합니다.",
     "2026-10-13"),
    ("manual-brand", "manual", "브랜드평판(📊 추천) 사용법", "6. 브랜드평판(📊 추천) 사용법",
     "브랜드평판 탭의 카테고리 10종, 하루 한도, 응원 코멘트, 결과 요약 읽는 법을 설명합니다.",
     "2026-10-13"),
    ("manual-youtube", "manual", "유튜브(▶ 좋아요) 사용법", "7. 유튜브(▶ 좋아요) 사용법",
     "유튜브 탭의 최신댓글만 처리, 처리 영상 개수, 영상 URL 지정 옵션과 2단계 인증 대처를 설명합니다.",
     "2026-10-13"),
    ("manual-playlist", "manual", "재생목록(📃 노래) 사용법", "8. 재생목록(📃 노래) 사용법",
     "재생목록 이름·시간, 핵심/핵심+ 체크, 핵심영상 패턴 5종, 기존 영상만 삭제 기능을 설명합니다.",
     "2026-10-13"),
    ("manual-starplanet", "manual", "스타플래닛(⭐ 젤리) 사용법", "9. 스타플래닛(⭐ 젤리) 사용법",
     "스타플래닛 탭의 동영상·복권·쇼핑·플레이스 미션 선택과 키워드 기록 저장 기능을 설명합니다.",
     "2026-10-13"),
    ("manual-celebchamp", "manual", "셀럽챔프(🏆 장미) 사용법", "10. 셀럽챔프(🏆 장미) 사용법",
     "셀럽챔프 탭의 출석, 홈 룰렛, 무료충전소 룰렛, 쿠팡 룰렛·쿠팡 특가 미션과 출석 체크박스를 설명합니다.",
     "2026-10-13"),
    ("manual-auto", "manual", "무인 자동 실행", "11. 무인 자동 실행 (고급)",
     "--auto 옵션의 번호별 의미와 여러 기능 순차 실행, Windows 작업 스케줄러 등록 방법을 설명합니다.",
     "2026-10-13"),
    ("manual-faq", "manual", "문제 해결 / FAQ", "12. 문제 해결 / FAQ",
     "설치·암호, 휴대폰 연결, 실행 중 멈춤, 업데이트, 로그 파일 등 자주 묻는 질문과 해결 방법을 모았습니다.",
     "2026-10-13"),
    ("guide-usb-debugging", "guide", "제조사별 USB 디버깅 켜는 법", "제조사별 개발자 옵션·USB 디버깅 켜는 법",
     "삼성 갤럭시, 샤오미·레드미·포코, 구글 픽셀, LG 휴대폰에서 개발자 옵션과 USB 디버깅을 켜는 메뉴 위치를 정리했습니다.",
     "2026-10-13"),
    ("guide-connection", "guide", "휴대폰 연결이 안 될 때", "휴대폰이 PC에 연결되지 않을 때 점검 순서",
     "USB 디버깅을 켰는데도 PC가 휴대폰을 찾지 못할 때 케이블, 포트, 허용 팝업, 드라이버 순서로 원인을 좁히는 방법입니다.",
     "2026-10-13"),
    ("guide-playlist-patterns", "guide", "재생목록 패턴 고르기", "재생목록 핵심영상 패턴 5종 비교",
     "시간 내 중복 방지, 시간+연속 중복 방지, 퐁당퐁당, 퐁당당퐁당, 퐁당당당퐁당당 패턴의 배치 규칙과 고르는 기준을 예시와 함께 설명합니다.",
     "2026-10-13"),
    ("guide-unattended", "guide", "매일 자동으로 돌릴 때 준비", "매일 자동으로 돌릴 때 PC와 휴대폰 준비",
     "작업 스케줄러로 매일 무인 실행할 때 절전 모드, 화면 잠금, 휴대폰 화면 꺼짐, 결과 확인을 준비하는 방법입니다.",
     "2026-10-13"),
    ("changelog", "site", "업데이트 내역", "업데이트 내역",
     "매크로의 버전별 변경 내용을 날짜순으로 정리한 업데이트 기록입니다.",
     None),  # 날짜는 최신 버전 배포일을 쓴다
    ("about", "site", "소개 · 문의", "소개 · 문의",
     "이 사이트와 매크로가 무엇인지, 누가 관리하는지, 이용할 때 알아둘 점과 문의 방법을 안내합니다.",
     "2026-10-13"),
    ("privacy", "site", "개인정보처리방침", "개인정보처리방침",
     "이 사이트가 수집하는 정보, 광고 쿠키, 프로그램이 PC에 저장하는 정보에 대한 안내입니다.",
     "2026-10-13"),
]

GROUP_TITLES = {"manual": "사용 설명서", "guide": "가이드", "site": "사이트"}

VERSION_RE = re.compile(r"^(?:버전|v)\s*(\d+\.\d+\.\d+)\s*(?:[-:]\s*(.+))?$")
# 사용자에게 의미 없는 개발용 커밋은 업데이트 내역에서 뺀다.
INTERNAL_RE = re.compile(r"BOM|리브랜딩|gitignore|갤러리에|스크립트|build\.bat|admin|SECRET|테스트|리팩터|버전 번호|버전 되돌림", re.I)


def read_changelog_from_git(repo):
    """프로그램 저장소의 커밋 제목에서 버전별 변경 내용을 뽑는다(최신순)."""
    out = subprocess.run(
        ["git", "-C", str(repo), "log", "--reverse", "--date=short", "--format=%ad\t%s"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    entries, pending = [], []
    for line in out.splitlines():
        day, _, subject = line.partition("\t")
        m = VERSION_RE.match(subject.strip())
        if not m:
            if not INTERNAL_RE.search(subject):
                pending.append(subject.strip())
            continue
        version, desc = m.group(1), m.group(2)
        # 버전 커밋에 설명이 있으면 그걸 쓰고, 없으면 그 사이에 쌓인 커밋 제목을 쓴다.
        notes = [desc.strip()] if desc else pending[-6:]
        entries.append({"version": version, "date": day, "notes": notes})
        pending = []
    seen, unique = set(), []
    for e in reversed(entries):  # 되돌렸다가 다시 올린 버전은 최신 것만 남긴다
        if e["version"] not in seen:
            seen.add(e["version"])
            unique.append(e)
    return unique


def render_changelog(entries):
    parts = []
    for e in entries:
        notes = "".join(f"<li>{html.escape(n)}</li>" for n in e["notes"]) or "<li>안정성 개선</li>"
        parts.append(
            f'<div class="release"><h3>v{e["version"]} <span class="release-date">{e["date"]}</span></h3>'
            f"<ul>{notes}</ul></div>"
        )
    return "\n".join(parts)


def render_nav(current):
    parts = [f'<a class="brand" href="index.html">{SITE_NAME}</a>']
    for group, title in GROUP_TITLES.items():
        tag = "ol" if group == "manual" else "ul"
        parts.append(f'<p class="nav-group">{title}</p>\n<{tag}>')
        number = 0
        for slug, page_group, label, *_ in PAGES:
            if page_group != group:
                continue
            number += 1
            num = f'<span class="num">{number}.</span>' if group == "manual" else ""
            cls = "ch-link current" if slug == current else "ch-link"
            parts.append(f'<li><a class="{cls}" href="{slug}.html">{num}{label}</a></li>')
        parts.append(f"</{tag}>")
    return "\n".join(parts)


def render_prev_next(slug):
    chapters = [p for p in PAGES if p[1] == "manual"]
    slugs = [p[0] for p in chapters]
    if slug not in slugs:
        return ""
    i = slugs.index(slug)
    prev_html = next_html = '<span class="spacer"></span>'
    if i > 0:
        p = chapters[i - 1]
        prev_html = f'<a class="prev" href="{p[0]}.html"><span class="dir">← 이전</span>{p[3]}</a>'
    if i < len(chapters) - 1:
        n = chapters[i + 1]
        next_html = f'<a class="next" href="{n[0]}.html"><span class="dir">다음 →</span>{n[3]}</a>'
    return f'<div class="page-nav-footer">{prev_html}{next_html}</div>'


def page_url(slug):
    return SITE_URL + "/" if slug == "index" else f"{SITE_URL}/{slug}"


TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="google-adsense-account" content="{adsense}">
<meta name="google-site-verification" content="{site_verification}">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={adsense}"
     crossorigin="anonymous"></script>
<title>{full_title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{site_name}">
<meta property="og:title" content="{full_title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="page-shell">
    <input type="checkbox" id="navToggle" class="nav-toggle-checkbox">
    <div class="mobile-topbar">
      <label for="navToggle" class="nav-toggle-btn" aria-label="목차 열기">☰</label>
      <span class="mobile-topbar-title">{site_name}</span>
    </div>
    <nav class="sidenav">
{nav}
    </nav>
    <label for="navToggle" class="nav-backdrop" aria-hidden="true"></label>
    <main class="main-col">
      <header class="page-head">
        <p class="eyebrow">{eyebrow}</p>
      </header>
{body}
      {prev_next}
      <footer class="page-foot">
        <p>마지막 수정 <time datetime="{updated}">{updated}</time> · 프로그램 최신 버전 v{version}</p>
        <p><a href="about.html">소개 · 문의</a> · <a href="changelog.html">업데이트 내역</a> ·
        <a href="privacy.html">개인정보처리방침</a></p>
      </footer>
    </main>
  </div>
</body>
</html>
"""


def build(changelog_repo=None):
    changelog_path = SRC / "changelog.json"
    if changelog_repo:
        entries = read_changelog_from_git(changelog_repo)
        changelog_path.write_text(
            json.dumps(entries, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
        )
    entries = json.loads(changelog_path.read_text(encoding="utf-8"))
    latest = entries[0]

    # 지난 빌드의 생성물만 지운다(최상단에는 build.py 등 원본도 함께 있다).
    for old in OUT.glob("*.html"):
        old.unlink()
    if (OUT / "manual-assets").exists():
        shutil.rmtree(OUT / "manual-assets")
    shutil.copytree(SRC / "manual-assets", OUT / "manual-assets")
    shutil.copy(SRC / "style.css", OUT / "style.css")

    contact = CONTACT_HTML or (
        "프로그램과 실행 암호를 전달해 준 관리자에게 문의해 주세요. "
        "문의할 때는 사용 중인 버전과 로그창의 마지막 몇 줄을 함께 보내 주시면 원인을 빨리 찾을 수 있습니다."
    )
    tokens = {
        "{{VERSION}}": latest["version"],
        "{{VERSION_DATE}}": latest["date"],
        "{{CONTACT}}": contact,
        "{{CHANGELOG}}": render_changelog(entries),
        "{{RECENT_CHANGES}}": render_changelog(entries[:4]),
        "{{RELEASE_COUNT}}": str(len(entries)),
        "{{FIRST_DATE}}": entries[-1]["date"],
    }

    for slug, group, label, title, description, updated in PAGES:
        body = (SRC / "pages" / f"{slug}.html").read_text(encoding="utf-8")
        for token, value in tokens.items():
            body = body.replace(token, value)
        leftover = re.search(r"\{\{[A-Z_]+\}\}", body)
        if leftover:
            raise SystemExit(f"{slug}: 알 수 없는 치환 토큰 {leftover.group(0)}")
        page = TEMPLATE.format(
            adsense=ADSENSE_CLIENT,
            site_verification=GOOGLE_SITE_VERIFICATION,
            full_title=SITE_NAME if slug == "index" else f"{title} - {SITE_NAME}",
            description=html.escape(description, quote=True),
            url=page_url(slug),
            site_name=SITE_NAME,
            nav=render_nav(slug),
            eyebrow=GROUP_TITLES.get(group, SITE_NAME),
            body=body.rstrip("\n"),
            prev_next=render_prev_next(slug),
            updated=updated or latest["date"],
            version=latest["version"],
        )
        (OUT / f"{slug}.html").write_text(page, encoding="utf-8", newline="\n")

    # 본문 조각끼리의 내부 링크가 실제 페이지를 가리키는지 확인한다.
    slugs = {p[0] for p in PAGES}
    for path in OUT.glob("*.html"):
        for href in re.findall(r'href="([^"#:]+)\.html(?:#[^"]*)?"', path.read_text(encoding="utf-8")):
            if href not in slugs:
                raise SystemExit(f"{path.name}: 없는 페이지로 가는 링크 {href}.html")

    urls = "\n".join(
        f"  <url><loc>{page_url(slug)}</loc><lastmod>{updated or latest['date']}</lastmod></url>"
        for slug, *_rest, updated in PAGES
    )
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n",
        encoding="utf-8", newline="\n",
    )
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8", newline="\n"
    )
    (OUT / "ads.txt").write_text(
        f"google.com, {ADSENSE_CLIENT.removeprefix('ca-')}, DIRECT, f08c47fec0942fa0\n",
        encoding="utf-8", newline="\n",
    )
    print(f"사이트 생성 완료: 페이지 {len(PAGES)}개, 최신 버전 v{latest['version']} ({latest['date']}), {date.today()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--changelog", metavar="REPO", nargs="?", const="",
        help="업데이트 내역을 프로그램 저장소의 git 기록에서 다시 뽑는다(경로를 생략하면 .program-repo 파일에 적힌 경로)",
    )
    repo = parser.parse_args().changelog
    if repo == "":
        # 경로는 PC마다 다르므로 저장소에 올리지 않는 .program-repo 파일에 한 줄로 적어 둔다.
        local = ROOT / ".program-repo"
        if not local.exists():
            raise SystemExit(".program-repo 파일에 프로그램 저장소 경로를 한 줄로 적어 주세요.")
        repo = (ROOT / local.read_text(encoding="utf-8").strip()).resolve()
    build(repo)
