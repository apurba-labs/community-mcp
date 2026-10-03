import pytest

from community_mcp.agent.schemas import SupportedLocale
from community_mcp.demo import detect_locale


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        (
            "What is happening at the centenary event?",
            SupportedLocale.EN,
        ),
        (
            "শতবর্ষ অনুষ্ঠানের সময়সূচি কী?",
            SupportedLocale.BN,
        ),
        (
            "I can donate blood",
            SupportedLocale.EN,
        ),
        (
            "আমি রক্ত দিতে পারি",
            SupportedLocale.BN,
        ),
    ],
)
def test_detect_locale(
    message: str,
    expected: SupportedLocale,
) -> None:
    assert detect_locale(message) == expected
