from .base import BaseCartridge
import time


class WebMarketCartridge(BaseCartridge):
    name = "WEB_MARKET"

    async def run(self, goal, pool, ledger, mission_id):
        start = time.monotonic()
        try:
            results = await pool.searxng_search(goal, "general")
            ledger.record("searxng", "OK", int((time.monotonic()-start)*1000), len(results))
            top = results[:25]
            findings = [
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": r.get("content"),
                    "engine": r.get("engine"),
                }
                for r in top
            ]
            refs = [
                {"ref_id": f"web-{i}", "title": r.get("title"), "url": r.get("url")}
                for i, r in enumerate(top)
                if r.get("url")
            ]
            return {"cartridge": self.name, "findings": findings, "refs": refs}
        except Exception as e:
            ledger.record("searxng", "ERROR", int((time.monotonic()-start)*1000), 0, str(e))
            return {"cartridge": self.name, "findings": [], "refs": []}
