"""
Simple example of using the MCP client.
"""
import asyncio
import logging

from mcp_toolkit.client import MCPClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run the example."""
    # Create a client with a default MCP server
    client = MCPClient(sse_url="https://your-mcp-server.com/sse")

    try:
        # Initialize the client
        logger.info("Initializing MCP client...")
        await client.initialize()

        # List available tools
        logger.info("Listing available tools...")
        tools = await client.list_tools()
        logger.info(f"Available tools: {[tool.name for tool in tools]}")

        # Call a tool (replace with an actual tool from your server)
        logger.info("Calling web_search tool...")
        result = await client.call_tool("web_search", {"query": "Python MCP"})
        logger.info(f"Result: {result}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Close the client
        logger.info("Closing MCP client...")
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
