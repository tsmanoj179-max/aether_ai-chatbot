import pytest
from backend.app.providers.mock_provider import MockProvider

@pytest.mark.asyncio
async def test_mock_provider_generation():
    provider = MockProvider()
    assert provider.is_configured() is True
    assert await provider.health_check() is True

    models = await provider.list_models()
    assert len(models) >= 3
    assert models[0].id == "aether-mock-omni"

    res = await provider.generate(
        messages=[{"role": "user", "content": "Can you write python code?"}],
        model="aether-mock-code"
    )
    assert res["provider_used"] == "mock"
    assert "```python" in res["content"]
    assert "Simulated Response" in res["content"]

@pytest.mark.asyncio
async def test_mock_provider_streaming():
    provider = MockProvider()
    tokens = []
    async for chunk in provider.generate_stream(
        messages=[{"role": "user", "content": "Hello AetherAI"}],
        model="aether-mock-omni"
    ):
        if chunk["type"] == "token":
            tokens.append(chunk["data"]["token"])
        elif chunk["type"] == "done":
            assert chunk["data"]["model_used"] == "aether-mock-omni"

    full_text = "".join(tokens)
    assert len(full_text) > 20
    assert "AetherAI" in full_text
