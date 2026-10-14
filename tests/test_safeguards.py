"""MarketLens - Safeguards and Ethics Unit Tests.

Tests robots.txt parsing, access barrier detection,
non-circumvention triggers, and PII auditing.
"""

from unittest.mock import MagicMock
import pytest
import requests
from marketlens.safeguards import EthicalScrapingGuard, RobotsChecker


def test_ethical_guard_detects_403_and_429() -> None:
    """Test that HTTP 403 and 429 are identified as access restrictions."""
    mock_resp_403 = MagicMock(spec=requests.Response)
    mock_resp_403.status_code = 403
    mock_resp_403.reason = "Forbidden"
    mock_resp_403.text = "Forbidden"

    can_proceed, reason = EthicalScrapingGuard.inspect_response(mock_resp_403)
    assert can_proceed is False
    assert "Access Restricted: HTTP 403" in reason

    mock_resp_429 = MagicMock(spec=requests.Response)
    mock_resp_429.status_code = 429
    mock_resp_429.reason = "Too Many Requests"
    mock_resp_429.text = "Rate limit exceeded"

    can_proceed, reason = EthicalScrapingGuard.inspect_response(mock_resp_429)
    assert can_proceed is False
    assert "Rate Limited: HTTP 429" in reason


def test_ethical_guard_detects_captcha_challenge() -> None:
    """Test that CAPTCHA challenge HTML triggers immediate halt."""
    mock_resp_captcha = MagicMock(spec=requests.Response)
    mock_resp_captcha.status_code = 200
    mock_resp_captcha.text = "<html><body>Please complete the g-recaptcha below</body></html>"

    can_proceed, reason = EthicalScrapingGuard.inspect_response(mock_resp_captcha)
    assert can_proceed is False
    assert "Automated Security Barrier Detected" in reason


def test_pii_audit_detection() -> None:
    """Test auditing records for unintentional email/phone PII collection."""
    clean_record = {
        "title": "Data Analytics Guide",
        "author": "Jane Doe",
        "description": "Standard market data text.",
    }
    is_safe, flags = EthicalScrapingGuard.audit_record_for_pii(clean_record)
    assert is_safe is True
    assert len(flags) == 0

    pii_record = {
        "title": "Contact me at analyst@consultingfirm.com for details",
        "phone": "Call +1-555-123-4567",
    }
    is_safe, flags = EthicalScrapingGuard.audit_record_for_pii(pii_record)
    assert is_safe is False
    assert len(flags) == 2


def test_robots_checker_mock() -> None:
    """Test RobotsChecker can evaluate disallow directives."""
    checker = RobotsChecker("MarketLensBot/1.0")

    # Manually configure an in-memory robot parser
    from urllib.robotparser import RobotFileParser
    parser = RobotFileParser()
    parser.parse([
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /private/",
        "Allow: /public/",
    ])
    checker._parsers["https://mock-target.com"] = parser

    assert checker.is_allowed("https://mock-target.com/public/items") is True
    assert checker.is_allowed("https://mock-target.com/admin/settings") is False
    assert checker.is_allowed("https://mock-target.com/private/data") is False
