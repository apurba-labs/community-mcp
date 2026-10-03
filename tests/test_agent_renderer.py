from community_mcp.agent.renderer import BilingualRenderer
from community_mcp.agent.schemas import SupportedLocale


def test_confirmation_prompt_is_bilingual() -> None:
    renderer = BilingualRenderer()

    english = renderer.confirmation_required(
        SupportedLocale.EN
    )
    bangla = renderer.confirmation_required(
        SupportedLocale.BN
    )

    assert "confirmation" in english.lower()
    assert "নিশ্চিত" in bangla


def test_unknown_response_is_bilingual() -> None:
    renderer = BilingualRenderer()

    english = renderer.unknown(SupportedLocale.EN)
    bangla = renderer.unknown(SupportedLocale.BN)

    assert "couldn't understand" in english.lower()
    assert "বুঝতে পারিনি" in bangla
