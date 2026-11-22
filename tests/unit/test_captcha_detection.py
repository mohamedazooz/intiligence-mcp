from intiligence_mcp.acquisition.captcha.detector import detect_challenge
from intiligence_mcp.acquisition.captcha.escalation import escalate_challenge


def test_detects_turnstile():
    result = detect_challenge('<div class="cf-turnstile"></div>')
    assert result.detected and result.category == "captcha"


def test_non_challenge_page():
    assert not detect_challenge("<html><title>Article</title></html>").detected


def test_escalation_requires_operator():
    result = escalate_challenge("captcha")
    assert result.status == "requires_human_review" and result.requires_operator
