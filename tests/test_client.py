"""
Tests for the MCP client.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_toolkit.client import MCPClient, MCPServerModel


@pytest.fixture
def mcp_server():
    """Create a test MCP server."""
    return MCPServerModel(
        id=uuid.uuid4(),
        mcp_name="test_server",
        sse_url="https://example.com/mcp/test",
        user_id="test_user",
        inactive=False,
        type="sse",
        source="test",
    )


@pytest.mark.asyncio
async def test_mcp_client_initialization(mcp_server):
    """Test MCP client initialization."""
    with patch('mcp_toolkit.client.client_manager.sse_client') as mock_sse_client, \
         patch('mcp_toolkit.client.client_manager.ClientSession') as mock_client_session:
        
        # Set up mocks
        mock_transport = AsyncMock()
        mock_transport.__aenter__.return_value = (AsyncMock(), AsyncMock())
        mock_sse_client.return_value = mock_transport
        
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_client_session.return_value = mock_session
        
        # Create client
        client = MCPClient(sse_url=mcp_server.sse_url)
        
        # Initialize client
        await client.initialize()
        
        # Check that sse_client was called with the correct URL
        mock_sse_client.assert_called_once_with(url=mcp_server.sse_url)
        
        # Check that initialize was called on the session
        mock_session.initialize.assert_called_once()


@pytest.mark.asyncio
async def test_mcp_client_list_tools(mcp_server):
    """Test MCP client list_tools method."""
    with patch('mcp_toolkit.client.client_manager.sse_client') as mock_sse_client, \
         patch('mcp_toolkit.client.client_manager.ClientSession') as mock_client_session:
        
        # Set up mocks
        mock_transport = AsyncMock()
        mock_transport.__aenter__.return_value = (AsyncMock(), AsyncMock())
        mock_sse_client.return_value = mock_transport
        
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_client_session.return_value = mock_session
        
        # Set up mock tools
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool"
        mock_tool.inputSchema = {"type": "object", "properties": {}}
        
        mock_tools = MagicMock()
        mock_tools.tools = [mock_tool]
        mock_session.list_tools.return_value = mock_tools
        
        # Create client
        client = MCPClient(sse_url=mcp_server.sse_url)
        
        # Initialize client
        await client.initialize()
        
        # List tools
        tools = await client.list_tools()
        
        # Check that list_tools was called on the session
        mock_session.list_tools.assert_called_once()
        
        # Check that the tools were returned
        assert len(tools) == 1
        assert tools[0].name == "test_tool"


@pytest.mark.asyncio
async def test_mcp_client_call_tool(mcp_server):
    """Test MCP client call_tool method."""
    with patch('mcp_toolkit.client.client_manager.sse_client') as mock_sse_client, \
         patch('mcp_toolkit.client.client_manager.ClientSession') as mock_client_session:
        
        # Set up mocks
        mock_transport = AsyncMock()
        mock_transport.__aenter__.return_value = (AsyncMock(), AsyncMock())
        mock_sse_client.return_value = mock_transport
        
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_client_session.return_value = mock_session
        
        # Set up mock tool call result
        mock_result = MagicMock()
        mock_result.content = [MagicMock()]
        mock_result.content[0].text = "Test result"
        mock_session.call_tool.return_value = mock_result
        
        # Create client
        client = MCPClient(sse_url=mcp_server.sse_url)
        
        # Initialize client
        await client.initialize()
        
        # Call tool
        result = await client.call_tool("test_tool", {"param": "value"})
        
        # Check that call_tool was called on the session with the correct arguments
        mock_session.call_tool.assert_called_once_with("test_tool", arguments={"param": "value"})
        
        # Check that the result was returned
        assert result == "Test result"
