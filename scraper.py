from __future__ import annotations

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.yu.ac.kr/ice/board/notice.do"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SchoolNoticeBot/1.0)"}

# 상세 페이지 본문 셀렉터 후보 (순서대로 시도)
CONTENT_SELECTORS = [
    "div.board-view-content",
    "div.view-con",
    "div.b-content-box",
    "div.board-view",
    "article",
]


def fetch_ice_notices(offset: int = 0) -> list[dict]:
    list_url = f"{BASE_URL}?mode=list&article.offset={offset}"
    response = requests.get(list_url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    notices = []
    # articleNo가 href에 포함된 링크만 선택 (공지/일반 게시글 모두)
    for row in soup.select("table tbody tr"):
        title_tag = row.select_one("td a[href*='articleNo']")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        detail_link = BASE_URL + title_tag["href"]

        # 날짜는 4번째 td에서 바로 가져옴 (상세 페이지 불필요)
        tds = row.select("td")
        date_str = tds[3].get_text(strip=True) if len(tds) > 3 else ""

        try:
            detail_res = requests.get(detail_link, headers=HEADERS, timeout=10)
            detail_res.raise_for_status()
            detail_soup = BeautifulSoup(detail_res.text, "html.parser")

            content_text = ""
            for selector in CONTENT_SELECTORS:
                area = detail_soup.select_one(selector)
                if area:
                    content_text = area.get_text(separator="\n", strip=True)
                    break

            notices.append(
                {"title": title, "url": detail_link, "text": content_text, "date": date_str}
            )
            print(f"  수집: {title[:40]}")

        except requests.RequestException as e:
            print(f"[경고] 상세 페이지 로드 실패 ({detail_link}): {e}")
            continue

    return notices
