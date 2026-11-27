import html
import re
import httpx
from .config import settings
from .guard import validate_url

_TAG_RE = re.compile(r"<[^>]+>")
_NOISE_BLOCK_RE = re.compile(r"<(script|style|head|svg|noscript)[^>]*>.*?</\1>", re.I | re.S)
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_NL_RE = re.compile(r"\n{3,}")


def _clean_html(raw: str) -> str:
    text = _NOISE_BLOCK_RE.sub(" ", raw)
    text = re.sub(r"</(p|div|li|tr|h[1-6]|pre|code|br)\b[^>]*>", "\n", text, flags=re.I)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = _WS_RE.sub(" ", text)
    text = _NL_RE.sub("\n\n", text)
    return text.strip()


class ClientPool:
    def __init__(self):
        self.http = httpx.AsyncClient(timeout=20.0)

    async def searxng_search(self, query: str, categories: str = "general"):
        url = f"{settings.searxng_url}/search"
        r = await self.http.get(url, params={"q": query, "format": "json", "categories": categories})
        r.raise_for_status()
        return r.json().get("results", [])

    async def crawl4ai_fetch(self, url: str, max_chars: int | None = None):
        ok, reason = validate_url(url)
        if not ok:
            return {"error": reason}
        limit = max_chars if max_chars is not None else settings.max_response_tokens * 3
        try:
            r = await self.http.post(f"{settings.crawl4ai_url}/crawl", json={"urls": [url]})
            r.raise_for_status()
            data = r.json()
            results = data.get("results", [])
            if results:
                return results[0]
        except Exception:
            pass
        r = await self.http.get(url, follow_redirects=True)
        r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        text = _clean_html(r.text) if "html" in ctype.lower() else r.text
        return {
            "url": str(r.url),
            "status_code": r.status_code,
            "body": text[:limit],
            "truncated": len(text) > limit,
        }

    async def close(self):
        await self.http.aclose()
