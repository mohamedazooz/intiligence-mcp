import re
import uuid
from fastmcp import FastMCP
from .config import settings
from .memory import Memory
from .guard import validate_url
from .router import classify
from .clients import ClientPool
from .ledger import CoverageLedger
from .cartridges import (BuildCartridge, WebMarketCartridge, AlgoPapersCartridge, OsintDarkCartridge)

mcp = FastMCP("OmniPulse")
memory = Memory()
pool = ClientPool()

CARTRIDGE_MAP = {
    "BUILD": BuildCartridge(),
    "WEB_MARKET": WebMarketCartridge(),
    "ALGO_PAPERS": AlgoPapersCartridge(),
    "OSINT_DARK": OsintDarkCartridge(),
}


_GH_REPO_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+?)/?$")
_PRIORITY_DOMAINS = ("raw.githubusercontent.com", "github.com", "docs.rs", "docs.", "solana.stackexchange.com")


def _to_raw_url(url: str) -> str:
    if "github.com/" in url and "/blob/" in url:
        return url.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/")
    m = _GH_REPO_RE.match(url.strip())
    if m:
        return f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/HEAD/README.md"
    return url


def _compact_finding(item: dict | str) -> dict | str:
    if not isinstance(item, dict):
        return item
    content = (item.get("content") or "").strip()
    if len(content) > 280:
        content = content[:280] + "..."
    return {
        "title": item.get("title"),
        "url": item.get("url"),
        "content": content,
    }


def _source_rank(url: str) -> tuple[int, str]:
    u = url.lower()
    for i, dom in enumerate(_PRIORITY_DOMAINS):
        if dom in u:
            return (i, u)
    return (len(_PRIORITY_DOMAINS), u)


@mcp.tool
async def research_mission(goal: str, mode: str = "auto", depth: str = "standard", force_refresh: bool = False) -> dict:
    mission_id = str(uuid.uuid4())
    await memory.init()
    await memory.record_mission(mission_id, goal, mode, depth, status="running")
    ledger = CoverageLedger(mission_id)
    selected = classify(goal, mode)
    findings = []
    refs = []
    detected = []
    for cart_name in selected:
        cart = CARTRIDGE_MAP[cart_name]
        detected.append(cart_name)
        res = await cart.run(goal, pool, ledger, mission_id)
        findings.extend(res.get("findings", []))
        refs.extend(res.get("refs", []))

    compact_findings = [_compact_finding(f) for f in findings[:12]]
    compact_refs = [{"ref_id": r.get("ref_id"), "url": r.get("url")} for r in refs[:12] if r.get("url")]

    fetched_sources = []
    if depth in ("deep", "full"):
        seen_urls = set()
        prioritized = sorted(
            [r for r in refs if r.get("url")],
            key=lambda r: _source_rank(r.get("url", "")),
        )
        per_source_chars = max(2500, (settings.max_response_tokens * 3) // 3)
        for ref in prioritized:
            raw_url = _to_raw_url(ref.get("url", ""))
            if not raw_url or raw_url in seen_urls:
                continue
            seen_urls.add(raw_url)
            try:
                page = await pool.crawl4ai_fetch(raw_url, max_chars=per_source_chars)
                if page.get("body"):
                    fetched_sources.append({
                        "ref_id": ref.get("ref_id"),
                        "url": raw_url,
                        "body": page["body"],
                        "truncated": page.get("truncated", False),
                    })
            except Exception as e:
                fetched_sources.append({
                    "ref_id": ref.get("ref_id"),
                    "url": raw_url,
                    "error": str(e),
                })
            if len(fetched_sources) >= 3:
                break

    summary = {"mission_id": mission_id, "status": "completed", "detected_cartridges": detected,
               "executive_findings": compact_findings, "drillable_refs": compact_refs,
               "fetched_sources": fetched_sources,
               "coverage_receipt": ledger.to_list()}
    await memory.record_mission(mission_id, goal, mode, depth, status="completed", summary=summary, tokens=settings.max_response_tokens)
    return summary


@mcp.tool
async def deep_drill(ref_id: str, action: str, params: dict | None = None) -> dict:
    params = params or {}
    if action in ("stealth_scrape_url", "fetch_url"):
        url = params.get("url", "")
        ok, reason = validate_url(url)
        if not ok:
            return {"error": reason}
        data = await pool.crawl4ai_fetch(url)
        return {"ref_id": ref_id, "data": data}
    return {"ref_id": ref_id, "action": action, "status": "not_implemented"}


@mcp.tool
async def watch_pulse(operation: str, target: str = "", watch_type: str = "", cadence_hours: int = 24) -> dict:
    return {"operation": operation, "target": target, "status": "not_implemented"}


@mcp.tool
async def guard_check(url: str) -> dict:
    from .guard import validate_url
    ok, reason = validate_url(url)
    return {"url": url, "safe": ok, "reason": reason}


@mcp.tool
async def cache_stats() -> dict:
    return {"backend": "sqlite-wal", "path": settings.sqlite_path, "max_response_tokens": settings.max_response_tokens}
def main():
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
