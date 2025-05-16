"""
Example of integrating MCP with LLM providers (OpenAI and Anthropic).
"""
import asyncio
import logging
import os

import openai
from anthropic import AsyncAnthropic

from mcp_toolkit.client import MCPChat
from mcp_toolkit.client.constants import MessageType, MCPServerModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure API keys (replace with your actual keys)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your-openai-api-key")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "your-anthropic-api-key")

# Configure MCP servers
MCP_SERVERS = [
    MCPServerModel(
        id="00000000-0000-0000-0000-000000000001",
        mcp_name="web_search",
        sse_url="https://example.com/mcp/web_search",
        user_id="system",
        inactive=False,
        type="sse",
        source="system",
    ),
]


async def openai_example():
    """Example of using MCP with OpenAI."""
    logger.info("Running OpenAI example...")

    # Initialize OpenAI client
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

    # Create messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant that can use tools."},
        {"role": "user", "content": "Search for information about Python programming language."}
    ]

    # Create MCP chat processor
    processor = MCPChat(
        model="gpt-4",
        messages=messages,
        stream=True,
        client=client,
        max_turns=3,
        user_data={"userId": "example_user"},
        mcp_servers=MCP_SERVERS
    )

    # Process the chat with streaming
    stream = processor.create_openai_stream(
        model="gpt-4",
        messages=messages,
        stream=True,
        client=client,
        max_turns=3,
        user_data={"userId": "example_user"},
        mcp_servers=MCP_SERVERS
    )

    # Print the streaming response
    async for chunk in stream:
        if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta'):
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content:
                print(delta.content, end="", flush=True)
        elif hasattr(chunk, 'model_dump'):
            # Custom progress chunks
            dump = chunk.model_dump()
            if 'choices' in dump and dump['choices'] and 'delta' in dump['choices'][0]:
                delta = dump['choices'][0]['delta']
                if 'content' in delta and 'type' in delta['content']:
                    if delta['content']['type'] == MessageType.PROGRESS:
                        print(f"\n[Progress: {delta['content']['content']}]")

    print("\n")


async def anthropic_example():
    """Example of using MCP with Anthropic."""
    logger.info("Running Anthropic example...")

    # Initialize Anthropic client
    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    # Create messages
    messages = [
        {"role": "user", "content": "Search for information about Python programming language."}
    ]

    # Create MCP chat processor
    processor = MCPChat(
        model="claude-3-opus-20240229",
        messages=messages,
        stream=True,
        client=client,
        max_turns=3,
        user_data={"userId": "example_user"},
        system_message="You are a helpful assistant that can use tools.",
        max_tokens=1000,
        mcp_servers=MCP_SERVERS
    )

    # Process the chat with streaming
    stream = processor.create_anthropic_stream(
        model="claude-3-opus-20240229",
        messages=messages,
        stream=True,
        client=client,
        max_turns=3,
        user_data={"userId": "example_user"},
        system_message="You are a helpful assistant that can use tools.",
        max_tokens=1000,
        mcp_servers=MCP_SERVERS
    )

    # Print the streaming response
    async for chunk in stream:
        if hasattr(chunk, 'type'):
            if chunk.type == 'content_block_delta' and hasattr(chunk, 'delta'):
                if hasattr(chunk.delta, 'text') and chunk.delta.text:
                    print(chunk.delta.text, end="", flush=True)
        elif hasattr(chunk, 'model_dump'):
            # Custom progress chunks
            dump = chunk.model_dump()
            if 'type' in dump and 'payload' in dump:
                if dump['type'] == MessageType.PROGRESS:
                    print(f"\n[Progress: {dump['payload']['content']}]")

    print("\n")


async def main():
    """Run the examples."""
    try:
        await openai_example()
        await anthropic_example()
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
