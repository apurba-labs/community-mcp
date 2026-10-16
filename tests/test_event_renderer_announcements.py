from community_mcp.agent.schemas import SupportedLocale
from community_mcp.simulator.event_renderer import (
    detect_event_topic,
    render_event_answer,
)


def test_bengali_unannounced_event_date():
    result = render_event_answer(
        {"title": "শতবর্ষ উদ্‌যাপন", "starts_at": None},
        topic="date",
        locale=SupportedLocale.BN,
    )

    assert "২২ অক্টোবর ২০২৬" in result
    assert "সম্ভাব্য তারিখ" in result
    assert "https://chandaikonamlhs.org/news" in result


def test_bengali_registration_explains_separate_processes():
    result = render_event_answer(
        {"registration_enabled": False},
        topic="registration",
        locale=SupportedLocale.BN,
    )

    assert "অ্যাকাউন্ট" in result
    assert "দুটি আলাদা প্রক্রিয়া" in result
    assert "https://chandaikonamlhs.org/news" in result


def test_registration_enabled_does_not_show_closed_message():
    result = render_event_answer(
        {"registration_enabled": True},
        topic="registration",
        locale=SupportedLocale.BN,
    )

    assert "চালু আছে" in result
    assert "শুরু হয়নি" not in result


def test_bengali_registration_question_detected():
    assert (
        detect_event_topic("নিবন্ধন কীভাবে করব?")
        == "registration"
    )


def test_bengali_date_question_detected():
    assert (
        detect_event_topic("শতবর্ষ উদযাপনের তারিখ কবে?")
        == "date"
    )