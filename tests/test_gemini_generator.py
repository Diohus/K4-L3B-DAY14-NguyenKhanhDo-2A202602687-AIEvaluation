"""Check the external API boundary without sending a paid or free-tier request."""

from types import SimpleNamespace
from unittest.mock import patch

from domain_assistant import GeminiGenerator, _configured_generator


def test_gemini_uses_openai_compatible_chat_api(monkeypatch):
    monkeypatch.setenv("GENERATOR_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    with patch("domain_assistant.OpenAI") as client_class:
        client_class.return_value.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="  Grounded answer  "))]
        )
        generator = _configured_generator()
        answer = generator.generate("Question and retrieved context")

    assert isinstance(generator, GeminiGenerator)
    assert answer == "Grounded answer"
    client_class.assert_called_once_with(
        api_key="test-key",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    client_class.return_value.chat.completions.create.assert_called_once_with(
        model="gemini-3.5-flash-lite",
        messages=[{"role": "user", "content": "Question and retrieved context"}],
        temperature=0,
        max_tokens=512,
    )
