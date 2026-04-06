from bs4 import BeautifulSoup


def get_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def extract_page_info(html: str) -> dict:
    soup = get_soup(html)
    text = soup.get_text(" ", strip=True)

    return {
        "title": soup.title.get_text(strip=True) if soup.title else "",
        "a_count": len(soup.select("a[href]")),
        "contains_review_word": "리뷰" in text,
        "contains_keyword": "수분크림" in text,
        "text_preview": text[:500],
    }
