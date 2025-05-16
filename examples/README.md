# MCP Toolkit Examples

This directory contains examples of how to use the MCP Toolkit.

## Simple Client Example

The `simple_client.py` file demonstrates how to use the MCP client to connect to an MCP server and call tools.

```bash
python simple_client.py
```

## FastAPI Integration Example

The `fastapi_integration.py` file demonstrates how to integrate MCP with FastAPI, including database integration for storing MCP configurations.

```bash
python fastapi_integration.py
```

This will start a FastAPI server on port 8000. You can access the API documentation at http://localhost:8000/docs.

## LLM Integration Example

The `llm_integration.py` file demonstrates how to integrate MCP with LLM providers (OpenAI and Anthropic).

```bash
# Set your API keys
export OPENAI_API_KEY=your-openai-api-key
export ANTHROPIC_API_KEY=your-anthropic-api-key

python llm_integration.py
```

## Customizing the Examples

These examples are meant to be starting points. You'll need to:

1. Replace the example MCP server URLs with your actual MCP server URLs
2. Provide your own API keys for OpenAI and Anthropic
3. Modify the database configuration for the FastAPI example if needed

## Running Your Own MCP Server

To run your own MCP server, you can use the [MCP](https://github.com/mcp-project/mcp) package. See the MCP documentation for details on how to set up and run an MCP server.
