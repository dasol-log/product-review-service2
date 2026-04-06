import requests


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_page(url: str, timeout: int = 15) -> requests.Response:
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=timeout
    )
    response.raise_for_status()
    return response