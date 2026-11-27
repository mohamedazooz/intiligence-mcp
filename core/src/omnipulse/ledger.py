import time


class CoverageLedger:
    def __init__(self, mission_id: str):
        self.mission_id = mission_id
        self.entries = []

    def record(self, adapter, status, latency_ms=0, items=0, note=""):
        self.entries.append({
            "source": adapter, "status": status, "latency_ms": latency_ms,
            "items_found": items, "reason": note,
        })

    def to_list(self):
        return self.entries


async def timed(coro):
    start = time.monotonic()
    try:
        res = await coro
        return res, int((time.monotonic() - start) * 1000), None
    except Exception as e:
        return None, int((time.monotonic() - start) * 1000), str(e)
