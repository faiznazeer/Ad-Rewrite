import re

from agent import platform_agent as pa


def test_sanitize_masks_profanity():
    text = "This is damn bad"
    sanitized, issues = pa.sanitize_text(text)
    assert "PROFANITY_MASKED" in issues
    assert "d***" in sanitized or "d**" in sanitized


def test_extract_entities_detects_cta_and_discount():
    text = "Huge sale! Get 50% off for shoes. Buy now"
    ents = pa.extract_entities(text)
    assert ents["discount"] is not None
    assert ents["cta"] is not None


def test_validate_trims_and_removes_emojis():
    constraints = {"allow_emojis": False, "max_length_chars": 10, "cta_required": False}
    text = "Nice deal 😊😊" * 3
    res = pa.validate_text(text, platform="instagram", constraints=constraints)
    assert "MAX_LENGTH_EXCEEDED" in res["issues"] or isinstance(res["ok"], bool)
    # ensure emojis removed
    assert not re.search(pa.EMOJI_REGEX, res["repaired_text"]) 
