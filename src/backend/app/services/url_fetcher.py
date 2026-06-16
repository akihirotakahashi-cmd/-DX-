"""
URL からテキストコンテンツを取得するサービス。
Google Drive / Google Sheets / Google Docs / 一般Webページ 対応。
"""
import re

import httpx
from bs4 import BeautifulSoup

_MAX_CHARS = 15000
_TIMEOUT = 20.0
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; chihousousei-dx/1.0)"}


def _to_export_url(url: str) -> str | None:
    """Google Workspace / Drive の URL をエクスポート URL に変換する。"""

    # Google Sheets
    m = re.match(r"https://docs\.google\.com/spreadsheets/d/([^/?#]+)", url)
    if m:
        return (
            f"https://docs.google.com/spreadsheets/d/{m.group(1)}"
            "/export?format=csv&gid=0"
        )

    # Google Docs
    m = re.match(r"https://docs\.google\.com/document/d/([^/?#]+)", url)
    if m:
        return f"https://docs.google.com/document/d/{m.group(1)}/export?format=txt"

    # Google Slides
    m = re.match(r"https://docs\.google\.com/presentation/d/([^/?#]+)", url)
    if m:
        return (
            f"https://docs.google.com/presentation/d/{m.group(1)}/export/txt"
        )

    # Google Drive ファイル（/file/d/ID/view など）
    m = re.search(r"drive\.google\.com/file/d/([^/?#]+)", url)
    if m:
        return (
            f"https://drive.google.com/uc?export=download&id={m.group(1)}&confirm=t"
        )

    # Google Drive open?id=...
    m = re.search(r"drive\.google\.com/open\?id=([^&]+)", url)
    if m:
        return (
            f"https://drive.google.com/uc?export=download&id={m.group(1)}&confirm=t"
        )

    return None


def _strip_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)


async def fetch_url_content(url: str) -> str:
    """URL のテキストコンテンツを取得して返す。"""
    fetch_url = _to_export_url(url) or url

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=_TIMEOUT,
            headers=_HEADERS,
        ) as client:
            resp = await client.get(fetch_url)

            # 403 はほぼ「非公開」なので分かりやすいメッセージを返す
            if resp.status_code == 403:
                return (
                    f"[アクセス拒否 (403): {url}\n"
                    "→ Google Drive / Sheets の場合は"
                    "「リンクを知っている全員が閲覧可」に変更してください]"
                )

            resp.raise_for_status()

            ctype = resp.headers.get("content-type", "")

            if "text/html" in ctype:
                return _strip_html(resp.text)[:_MAX_CHARS]

            if "application/pdf" in ctype:
                from app.services.file_extractor import _extract_pdf
                return _extract_pdf(resp.content)[:_MAX_CHARS]

            # CSV / plain text など
            return resp.text[:_MAX_CHARS]

    except httpx.HTTPStatusError as e:
        return f"[HTTP {e.response.status_code} エラー: {url}]"
    except httpx.TimeoutException:
        return f"[タイムアウト ({_TIMEOUT}秒): {url}]"
    except Exception as e:
        return f"[取得エラー: {url} — {e}]"


async def fetch_all(urls: list[str]) -> list[tuple[str, str]]:
    """複数 URL を並列取得して (url, content) のリストを返す。"""
    import asyncio

    valid = [u for u in urls if u.strip()]
    if not valid:
        return []
    results = await asyncio.gather(*(fetch_url_content(u) for u in valid))
    return list(zip(valid, results))
