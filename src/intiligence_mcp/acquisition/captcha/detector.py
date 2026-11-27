"""Conservative detection of access challenges and non-public page gates."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChallengeResult:
    detected: bool
    category: str
    evidence: tuple[str, ...]


_MARKERS = {
    "captcha": ("captcha", "g-recaptcha", "h-captcha", "cf-turnstile", "arkose"),
    "bot_challenge": (
        "checking your browser",
        "verify you are human",
        "attention required",
        "challenge-platform",
        "cf-chl-",
        "automated requests",
    ),
    "authentication": (
        "authentication required",
        "sign in to continue",
        "log in to continue",
        "please log in",
    ),
    "paywall": (
        "subscribe to continue",
        "subscription required",
        "purchase access",
        "metered paywall",
    ),
    "rate_limit": (
        "too many requests",
        "rate limit exceeded",
        "temporarily blocked",
    ),
}


def detect_challenge(html: str, title: str = "") -> ChallengeResult:
    sample = (title + "\n" + html[:1_000_000]).lower()
    for category, markers in _MARKERS.items():
        found = tuple(marker for marker in markers if marker in sample)
        if found:
            return ChallengeResult(True, category, found)
    return ChallengeResult(False, "none", ())
