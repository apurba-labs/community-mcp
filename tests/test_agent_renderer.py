import pytest

from community_mcp.agent.renderer import BilingualRenderer
from community_mcp.agent.schemas import SupportedLocale
from community_mcp.providers.demo import DemoProvider


def test_confirmation_prompt_is_bilingual() -> None:
    renderer = BilingualRenderer()

    english = renderer.confirmation_required(SupportedLocale.EN)
    bangla = renderer.confirmation_required(SupportedLocale.BN)

    assert "confirmation" in english.lower()
    assert "নিশ্চিত" in bangla


def test_unknown_response_is_bilingual() -> None:
    renderer = BilingualRenderer()

    english = renderer.unknown(SupportedLocale.EN)
    bangla = renderer.unknown(SupportedLocale.BN)

    assert "couldn't understand" in english.lower()
    assert "বুঝতে পারিনি" in bangla


@pytest.mark.asyncio
async def test_event_renderer_uses_event_program() -> None:
    event = await DemoProvider().get_event_by_slug("centenary-celebration")

    message = BilingualRenderer().event_context(
        event,
        SupportedLocale.EN,
    )

    assert event.title in message
    assert event.program[0].title in message


@pytest.mark.asyncio
async def test_event_renderer_handles_unconfirmed_date_and_empty_program() -> None:
    event = await DemoProvider().get_event_by_slug("centenary-celebration")

    event = event.model_copy(
        update={
            "starts_at": None,
            "program": [],
        }
    )

    renderer = BilingualRenderer()

    english = renderer.event_context(event, SupportedLocale.EN)
    bangla = renderer.event_context(event, SupportedLocale.BN)

    assert event.title in english
    assert "date has not yet been confirmed" in english
    assert "Main activities:" not in english

    assert event.title in bangla
    assert "তারিখ এখনো নিশ্চিত করা হয়নি" in bangla
    assert "প্রধান কার্যক্রম:" not in bangla
