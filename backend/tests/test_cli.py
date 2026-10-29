import pytest
from backend.app.cli.main import AetherCLI

@pytest.mark.asyncio
async def test_cli_initialization():
    cli = AetherCLI(model="gemini-2.5-flash", persona="general")
    assert cli.model == "gemini-2.5-flash"
    assert cli.persona == "general"
    assert cli.conversation_id is not None
    assert len(cli.messages) == 0

@pytest.mark.asyncio
async def test_cli_slash_commands():
    cli = AetherCLI(model="gemini-2.5-flash")

    # Test /model
    handled = await cli.handle_slash_command("/model gpt-4o")
    assert handled is True
    assert cli.model == "gpt-4o"

    # Test /persona
    handled = await cli.handle_slash_command("/persona coder")
    assert handled is True
    assert cli.persona == "coder"

    # Test /help
    handled = await cli.handle_slash_command("/help")
    assert handled is True

    # Test /clear or /new
    old_id = cli.conversation_id
    handled = await cli.handle_slash_command("/new")
    assert handled is True
    assert cli.conversation_id != old_id

    # Test /exit
    handled = await cli.handle_slash_command("/exit")
    assert handled is False

@pytest.mark.asyncio
async def test_cli_tools_and_memory():
    cli = AetherCLI()

    # Tool execution
    await cli.execute_tool("calculator 45 * 2")
    await cli.execute_tool("datetime")

    # Memory handling
    await cli.handle_memory("add User prefers dark mode and Python")
    await cli.handle_memory("list")
    await cli.handle_memory("clear")
