import pytest
from backend.app.services.tool_registry import tool_registry

@pytest.mark.asyncio
async def test_calculator_tool():
    # Valid math
    res = await tool_registry.execute_tool("calculator", {"expression": "(12 * 5) + (100 / 4) - 5"})
    assert res["result"] == 80.0

    # Division by zero protection
    res_zero = await tool_registry.execute_tool("calculator", {"expression": "50 / 0"})
    assert "error" in res_zero

    # Forbidden execution protection (e.g. __import__)
    res_malicious = await tool_registry.execute_tool("calculator", {"expression": "__import__('os').system('ls')"})
    assert "error" in res_malicious

@pytest.mark.asyncio
async def test_datetime_tool():
    res = await tool_registry.execute_tool("datetime_util", {"action": "current_time"})
    assert "utc_now" in res
    assert "formatted" in res
