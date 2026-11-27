import re

CARTRIDGES = ["BUILD", "WEB_MARKET", "ALGO_PAPERS", "OSINT_DARK"]

OSINT_PATTERNS = [
    r"\.onion\b", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b", r"wallet|bitcoin|ethereum|0x[a-fA-F0-9]{40}",
    r"leak|breach|ransomware|darknet|osint",
]
BUILD_PATTERNS = [r"build|scaffold|framework|library|docs|upgrade|repo|github", r"fastapi|rust|next|react|python"]
ALGO_PATTERNS = [r"paper|arxiv|algorithm|research|latex|model"]


def classify(goal: str, mode: str = "auto") -> list[str]:
    if mode and mode != "auto":
        mapping = {
            "build": ["BUILD"], "web_market": ["WEB_MARKET"],
            "algo_papers": ["ALGO_PAPERS"], "osint_dark": ["OSINT_DARK"],
            "hybrid": CARTRIDGES,
        }
        return mapping.get(mode, ["WEB_MARKET"])
    g = goal.lower()
    selected = []
    if any(re.search(p, g, re.I) for p in OSINT_PATTERNS):
        selected.append("OSINT_DARK")
    if any(re.search(p, g, re.I) for p in ALGO_PATTERNS):
        selected.append("ALGO_PAPERS")
    if any(re.search(p, g, re.I) for p in BUILD_PATTERNS):
        selected.append("BUILD")
    if not selected or selected == ["BUILD"]:
        if "WEB_MARKET" not in selected:
            selected.insert(0, "WEB_MARKET")
    return selected
