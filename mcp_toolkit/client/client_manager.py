"""
Client manager for MCP servers.
"""
import logging
from contextlib import AsyncExitStack
from typing import Dict, List, Any, Tuple, Optional

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

# Set up logging
logger = logging.getLogger(__name__)


class MCPClient:
    """
    A simplified client for connecting to a single MCP server.
    
    This class provides a simpler interface for applications that only need
    to connect to a single MCP server.
    """

    def __init__(self, sse_url: Optional[str] = None, stdio_params: Optional[Dict] = None):
        """
        Initialize the MCP client.
        
        Args:
            sse_url: URL for the SSE server
            stdio_params: Parameters for stdio connection
        """
        if not sse_url and not stdio_params:
            raise ValueError("Either sse_url or stdio_params must be provided")

        self.sse_url = sse_url
        self.stdio_params = stdio_params
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def initialize(self):
        """Initialize the client connection."""
        try:
            if self.sse_url:
                sse_transport = await self.exit_stack.enter_async_context(
                    sse_client(url=self.sse_url)
                )
                read, write = sse_transport
            else:
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(self.stdio_params)
                )
                read, write = stdio_transport

            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await self.session.initialize()
            return self.session
        except Exception as e:
            logger.error(f"Error initializing MCP client: {e}")
            raise

    async def list_tools(self):
        """List available tools from the MCP server."""
        if not self.session:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        tools = await self.session.list_tools()
        return tools.tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            The result of the tool call
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        result = await self.session.call_tool(tool_name, arguments=arguments)
        return result.content[0].text

    async def close(self):
        """Close the client connection."""
        await self.exit_stack.aclose()


class MultipleMCPClientManager:
    """
    Manager for multiple MCP client connections.
    
    This class manages connections to multiple MCP servers and provides
    a unified interface for listing and calling tools across all servers.
    """

    def __init__(self, stdio_server_map: Dict[str, Dict], sse_server_map: List[Any]):
        """
        Initialize the MCP client manager.
        
        Args:
            stdio_server_map: Map of server names to stdio connection parameters
            sse_server_map: List of MCP server configurations with sse_url
        """
        self.stdio_server_map = stdio_server_map
        self.sse_server_map = sse_server_map
        self.sessions = {}
        self.exit_stack = AsyncExitStack()

    async def initialize(self):
        """Initialize connections to all configured MCP servers."""
        # Initialize stdio connections
        try:
            for server_name, params in self.stdio_server_map.items():
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(params)
                )
                read, write = stdio_transport
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                await session.initialize()
                self.sessions[server_name] = session

            # Initialize SSE connections
            for mcp in self.sse_server_map:
                sse_transport = await self.exit_stack.enter_async_context(
                    sse_client(url=mcp.sse_url)
                )
                read, write = sse_transport
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                await session.initialize()
                self.sessions[mcp.mcp_name] = session
        except Exception as e:
            logger.error(f"Error initializing MCP client manager: {e}")
            raise

    async def list_tools(self) -> Tuple[Dict[str, str], List[Any]]:
        """
        List all available tools across all MCP servers.
        
        Returns:
            A tuple containing:
            - tool_map: Mapping of tool names to server names
            - consolidated_tools: List of all tool objects
        """
        tool_map = {}
        consolidated_tools = []

        for server_name, session in self.sessions.items():
            tools = await session.list_tools()

            # Only add tools that don't already exist in the tool_map
            for tool in tools.tools:
                if tool.name not in tool_map:
                    tool_map[tool.name] = server_name
                    consolidated_tools.append(tool)

        return tool_map, consolidated_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], tool_map: Dict[str, str]) -> Optional[str]:
        """
        Call a tool on the appropriate MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            tool_map: Mapping of tool names to server names
            
        Returns:
            The result of the tool call, or None if the tool is not found
        """
        server_name = tool_map.get(tool_name)
        if not server_name:
            logger.error(f"Tool '{tool_name}' not found.")
            return None

        session = self.sessions.get(server_name)
        if session:
            result = await session.call_tool(tool_name, arguments=arguments)
            return result.content[0].text
        return None

    async def close(self):
        """Close all client connections."""
        await self.exit_stack.aclose()
