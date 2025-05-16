# MCP Toolkit

MCP Toolkit is a Python library for interacting with Model-Controller-Persistence (MCP) servers. It provides a client for connecting to MCP servers and a configuration system for managing MCP server connections.

## Features

- **MCP Client**: Connect to MCP servers via SSE (Server-Sent Events) or stdio
- **Tool Management**: List and call tools provided by MCP servers
- **LLM Integration**: Format tool responses for OpenAI and Anthropic models
- **Configuration Management**: Store and retrieve MCP server configurations

## Installation

```bash
pip install mcp-toolkit
```

## Quick Start

### Basic Usage

```python
import asyncio
from mcp_toolkit.client import MCPClient

async def main():
    # Create a client with a default MCP server
    client = MCPClient(sse_url="https://your-mcp-server.com/sse")
    
    # Initialize the client
    await client.initialize()
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {tools}")
    
    # Call a tool
    result = await client.call_tool("web_search", {"query": "Python MCP"})
    print(f"Result: {result}")
    
    # Close the client
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Integration with LLMs

```python
import asyncio
from mcp_toolkit.client import MCPChat

async def main():
    # Create messages for the chat
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Search for information about Python."}
    ]
    
    # Create a chat processor with OpenAI
    processor = MCPChat(
        model="gpt-4",
        messages=messages,
        user_data={"userId": "user123"},
        stream=True
    )
    
    # Process the chat with streaming
    async for chunk in processor.process_openai_stream_chat():
        print(chunk.model_dump())

if __name__ == "__main__":
    asyncio.run(main())
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from mcp_toolkit.configs import MCPRouter, get_mcp_service

app = FastAPI()

# Include the MCP router
app.include_router(MCPRouter, prefix="/api/v1")

@app.get("/tools")
async def list_tools(mcp_service = Depends(get_mcp_service)):
    """List all available tools from configured MCP servers."""
    tools = await mcp_service.list_all_tools()
    return {"tools": tools}
```

## Documentation

For more detailed documentation, see the [examples](./examples) directory.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
