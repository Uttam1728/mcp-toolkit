"""
Chat processing with MCP tools.
"""
import json
import logging
from typing import AsyncGenerator, Dict, List, Any, Optional, Union

from .chunks import OpenAICompatibleChunk, create_llm_chunk, AnthropicCompatibleChunk
from .client_manager import MultipleMCPClientManager
from .constants import BUILTIN_MCP_SERVERS, MessageType
from .helper import MCPHelper
from .streams import CustomAsyncStream

# Set up logging
logger = logging.getLogger(__name__)


class MCPChat:
    """
    Chat processor for integrating MCP tools with LLM providers.
    
    This class handles the integration between LLM chat completions and MCP tools,
    allowing tools to be called during chat completions.
    """
    
    def __init__(
            self,
            model: str,
            messages: List[Dict],
            stream: bool,
            client: Any,
            max_turns: int = 3,
            user_data: Optional[Dict] = None,
            temperature: Optional[float] = None,
            stream_options: Optional[Dict] = None,
            system_message: Optional[str] = None,
            max_tokens: Optional[int] = None,
            mcp_servers: Optional[List[Any]] = None
    ):
        """
        Initialize the MCP chat processor.
        
        Args:
            model: The model to use for chat completions
            messages: The messages to process
            stream: Whether to stream the response
            client: The LLM client (OpenAI or Anthropic)
            max_turns: Maximum number of tool call turns
            user_data: User data for MCP client
            temperature: Temperature for model generation
            stream_options: Options for streaming
            system_message: System message for Anthropic
            max_tokens: Maximum tokens for Anthropic
            mcp_servers: List of MCP servers to use (defaults to BUILTIN_MCP_SERVERS)
        """
        self.model = model
        self.messages = messages
        self.temperature = temperature
        self.stream = stream
        self.stream_options = stream_options or {}
        self.client = client
        self.max_turns = max_turns
        self.user_data = user_data or {}
        self.client_manager = None
        self.tool_map = None
        self.tools = None
        self.chat_messages = None
        self.system_message = system_message
        self.max_tokens = max_tokens
        self.mcp_servers = mcp_servers or BUILTIN_MCP_SERVERS

    async def setup_client(self, provider: str = 'openai') -> None:
        """
        Set up the MCP client and retrieve available tools.
        
        Args:
            provider: The LLM provider ('openai' or 'anthropic')
        """
        stdio_server_map = {}
        
        # Use the provided MCP servers
        sse_server_map = self.mcp_servers

        self.client_manager = MultipleMCPClientManager(stdio_server_map, sse_server_map)
        await self.client_manager.initialize()

        self.tool_map, tool_objects = await self.client_manager.list_tools()
        self.tools = MCPHelper.format_tools_object_for_llm_call(tool_objects, provider)
        self.chat_messages = self.messages[:]

    async def process_tool_calls(self, final_tool_calls: Dict, provider: str = 'openai') -> AsyncGenerator[
        Union[OpenAICompatibleChunk, AnthropicCompatibleChunk], None]:
        """
        Process tool calls and update chat messages.
        
        Args:
            final_tool_calls: Dictionary of tool calls to process
            provider: The LLM provider ('openai' or 'anthropic')
            
        Yields:
            Progress chunks during tool execution
        """
        if not final_tool_calls:
            return

        for i, tool_call in enumerate(final_tool_calls.values()):
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])

            yield create_llm_chunk(MessageType.PROGRESS, f"Executing tool: {tool_name}...",
                                   provider=provider)

            
            observation = await self.client_manager.call_tool(
                tool_name, tool_args, self.tool_map
            )

            tool_result_message = MCPHelper.create_tool_result_message(tool_call["id"], str(observation), provider)
            self.chat_messages.append(tool_result_message)

            yield create_llm_chunk(MessageType.PROGRESS, f"Tool {tool_name} execution complete.",
                                   provider=provider)

        yield create_llm_chunk(MessageType.PROGRESS, "All tools executed successfully.",
                               provider=provider)

    @classmethod
    def create_openai_stream(cls, **kwargs) -> CustomAsyncStream:
        """
        Create and return a custom stream object for MCP chat processing with OpenAI.

        Args:
            **kwargs: Arguments to pass to MCPChat constructor
            
        Returns:
            A stream of chat completion chunks
        """
        processor = cls(**kwargs)
        return CustomAsyncStream(processor.process_openai_stream_chat)

    @classmethod
    def create_openai_non_stream(cls, **kwargs) -> Any:
        """
        Create and process a non-streaming MCP chat with OpenAI.

        Args:
            **kwargs: Arguments to pass to MCPChat constructor
            
        Returns:
            The final chat completion response
        """
        processor = cls(**kwargs, stream=False, stream_options={})
        return processor.process_openai_non_stream_chat()

    async def process_openai_stream_chat(self) -> AsyncGenerator[OpenAICompatibleChunk, None]:
        """
        Process the chat with MCP tools using OpenAI.
        
        Yields:
            OpenAI-compatible chunks during processing
        """
        try:
            yield create_llm_chunk(MessageType.PROGRESS, "Warming up the thinking engine...",
                                   provider='openai')
            await self.setup_client()

            for turn in range(self.max_turns):
                # Create initial completion with tools
                if turn == 0:
                    yield create_llm_chunk(MessageType.PROGRESS,
                                           "Analyzing your question and determining next steps...",
                                           provider='openai')
                completion_params = {
                    "model": self.model,
                    "messages": self.chat_messages,
                    "tools": self.tools,
                    "stream": self.stream,
                }
                
                # Add optional parameters if provided
                if self.stream_options:
                    completion_params["stream_options"] = self.stream_options
                if self.temperature is not None:
                    completion_params["temperature"] = self.temperature

                # Call the OpenAI API
                stream_response = await self.client.chat.completions.create(**completion_params)

                # Collect tool calls while streaming response
                final_tool_calls = {}
                tool_index = 0
                current_tool_index = None
                content_buffer = ""

                async for chunk in stream_response:
                    try:
                        # Process tool calls from delta
                        if hasattr(chunk.choices[0].delta, 'tool_calls') and chunk.choices[0].delta.tool_calls:
                            for tool_call in chunk.choices[0].delta.tool_calls:
                                if tool_call.index not in final_tool_calls:
                                    # Initialize a new tool call
                                    final_tool_calls[tool_call.index] = {
                                        "id": tool_call.id or f"call_{tool_index}",
                                        "type": "function",
                                        "function": {
                                            "name": tool_call.function.name or "",
                                            "arguments": tool_call.function.arguments or ""
                                        }
                                    }
                                    tool_index += 1
                                else:
                                    # Update an existing tool call
                                    if tool_call.function.name:
                                        final_tool_calls[tool_call.index]["function"]["name"] = tool_call.function.name
                                    if tool_call.function.arguments:
                                        final_tool_calls[tool_call.index]["function"]["arguments"] += tool_call.function.arguments
                        
                        # Process content from delta
                        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                            content_buffer += chunk.choices[0].delta.content
                        
                        # Pass through the chunk
                        yield chunk
                    except Exception as e:
                        logger.error(f"Error processing chunk: {e}")
                        yield create_llm_chunk(MessageType.ERROR, f"Error processing response: {str(e)}",
                                               provider='openai')

                # Process tool calls from the response
                if final_tool_calls:
                    yield create_llm_chunk(MessageType.PROGRESS,
                                           "Using MCP tools to gather information...",
                                           provider='openai')

                    self.chat_messages.append(
                        {"role": "assistant", "content": None,
                         "tool_calls": MCPHelper.convert_to_openai_tool_format(final_tool_calls)}
                    )

                    async for tool_progress in self.process_tool_calls(final_tool_calls, provider='openai'):
                        yield tool_progress

                    yield create_llm_chunk(MessageType.PROGRESS,
                                           "Information gathered. Formulating complete response...",
                                           provider='openai')

                    follow_up_params = {
                        "model": self.model,
                        "messages": self.chat_messages,
                        "stream": self.stream,
                    }
                    
                    # Add optional parameters if provided
                    if self.stream_options:
                        follow_up_params["stream_options"] = self.stream_options
                    if self.temperature is not None:
                        follow_up_params["temperature"] = self.temperature

                    follow_up_response = await self.client.chat.completions.create(**follow_up_params)
                    async for chunk in follow_up_response:
                        yield chunk
                else:
                    # If no tool calls, we're done with this turn
                    if content_buffer:
                        self.chat_messages.append({"role": "assistant", "content": content_buffer})
                    break
            
        except Exception as e:
            logger.error(f"Error in process_openai_stream_chat: {e}")
            yield create_llm_chunk(MessageType.ERROR, f"Error: {str(e)}", provider='openai')

    async def process_openai_non_stream_chat(self) -> Any:
        """
        Process the chat with MCP tools using OpenAI in non-streaming mode.
        
        Returns:
            The final chat completion response
        """
        try:
            await self.setup_client()

            for turn in range(self.max_turns):
                # Create initial completion with tools
                completion_params = {
                    "model": self.model,
                    "messages": self.chat_messages,
                    "tools": self.tools,
                }
                
                # Add temperature if provided
                if self.temperature is not None:
                    completion_params["temperature"] = self.temperature

                # Call the OpenAI API
                response = await self.client.chat.completions.create(**completion_params)
                
                # Check for tool calls
                if response.choices[0].message.tool_calls:
                    # Format tool calls
                    tool_calls = {}
                    for i, tool_call in enumerate(response.choices[0].message.tool_calls):
                        tool_calls[i] = {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    
                    # Add assistant message with tool calls
                    self.chat_messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": MCPHelper.convert_to_openai_tool_format(tool_calls)
                    })
                    
                    # Process each tool call
                    for tool_call in tool_calls.values():
                        tool_name = tool_call["function"]["name"]
                        tool_args = json.loads(tool_call["function"]["arguments"])
                        
                        # Call the tool
                        observation = await self.client.manager.call_tool(
                            tool_name, tool_args, self.tool_map
                        )
                        
                        # Add tool result message
                        tool_result_message = MCPHelper.create_tool_result_message(
                            tool_call["id"], str(observation), 'openai'
                        )
                        self.chat_messages.append(tool_result_message)
                    
                    # Get final response
                    follow_up_params = {
                        "model": self.model,
                        "messages": self.chat_messages,
                    }
                    
                    # Add temperature if provided
                    if self.temperature is not None:
                        follow_up_params["temperature"] = self.temperature
                        
                    final_response = await self.client.chat.completions.create(**follow_up_params)
                    return final_response
                else:
                    # No tool calls, return the response
                    self.chat_messages.append({
                        "role": "assistant",
                        "content": response.choices[0].message.content
                    })
                    return response
            
            # If we've reached max turns, return the last response
            return response
            
        except Exception as e:
            logger.error(f"Error in process_openai_non_stream_chat: {e}")
            raise

    @classmethod
    def create_anthropic_stream(cls, **kwargs) -> CustomAsyncStream:
        """
        Create and return a custom stream object for MCP chat processing with Anthropic.

        Args:
            **kwargs: Arguments to pass to MCPChat constructor
            
        Returns:
            A stream of chat completion chunks
        """
        processor = cls(**kwargs)
        return CustomAsyncStream(processor.process_anthropic_stream_chat)

    async def process_anthropic_stream_chat(self) -> AsyncGenerator[AnthropicCompatibleChunk, None]:
        """
        Process the chat with MCP tools using Anthropic.
        
        Yields:
            Anthropic-compatible chunks during processing
        """
        try:
            yield create_llm_chunk(MessageType.PROGRESS, "Warming up the thinking engine...",
                                   provider='anthropic')
            await self.setup_client(provider="anthropic")

            for turn in range(self.max_turns):
                # Create initial completion with tools
                if turn == 0:
                    yield create_llm_chunk(MessageType.PROGRESS,
                                           "Analyzing your question and determining next steps...",
                                           provider='anthropic')
                completion_params = {
                    "model": self.model,
                    "messages": self.chat_messages,
                    "tools": self.tools,
                }
                
                # Add optional parameters if provided
                if self.max_tokens is not None:
                    completion_params["max_tokens"] = self.max_tokens
                if self.system_message is not None:
                    completion_params["system"] = self.system_message

                # Call the Anthropic API
                stream_response = await self.client.messages.stream(**completion_params).__aenter__()

                # Collect tool calls while streaming response
                final_tool_calls = {}
                tool_index = 0
                current_tool_index = None

                async for chunk in stream_response:
                    try:
                        # Anthropic format
                        if hasattr(chunk, 'type'):
                            if chunk.type == "content_block_start" and chunk.content_block.type == "tool_use":
                                # Start a new tool
                                index = tool_index
                                tool_index += 1
                                final_tool_calls[index] = {
                                    "id": chunk.content_block.id,
                                    "type": "function",
                                    "function": {
                                        "name": chunk.content_block.name,
                                        "arguments": ""
                                    }
                                }
                                # Store the current tool index being processed
                                current_tool_index = index
                            elif chunk.type == "content_block_delta" and hasattr(chunk.delta,
                                                                                 "type") and chunk.delta.type == "input_json_delta":
                                # Update the current tool being processed
                                if current_tool_index is not None and current_tool_index in final_tool_calls:
                                    final_tool_calls[current_tool_index]["function"][
                                        "arguments"] += chunk.delta.partial_json
                        yield chunk
                    except Exception as e:
                        logger.error(f"Error processing chunk: {e}")
                        yield create_llm_chunk(MessageType.ERROR, f"Error processing response: {str(e)}",
                                               provider='anthropic')

                # Process tool calls from the response
                if final_tool_calls:
                    self.chat_messages.append({
                        "role": "assistant",
                        "content": MCPHelper.convert_to_anthropic_tool_format(final_tool_calls)
                    })

                    yield create_llm_chunk(MessageType.PROGRESS,
                                           "Using MCP tools to gather information...",
                                           provider='anthropic')
                    async for tool_progress in self.process_tool_calls(final_tool_calls, provider='anthropic'):
                        yield tool_progress

                    yield create_llm_chunk(MessageType.PROGRESS,
                                           "Information gathered. Formulating complete response...",
                                           provider='anthropic')

                    follow_up_params = {
                        "model": self.model,
                        "messages": self.chat_messages,
                    }
                    
                    # Add optional parameters if provided
                    if self.max_tokens is not None:
                        follow_up_params["max_tokens"] = self.max_tokens
                    if self.system_message is not None:
                        follow_up_params["system"] = self.system_message

                    follow_up_response = await self.client.messages.stream(**follow_up_params).__aenter__()
                    async for chunk in follow_up_response:
                        yield chunk
                else:
                    # If no tool calls, we're done with this turn
                    break
            
        except Exception as e:
            logger.error(f"Error in process_anthropic_stream_chat: {e}")
            yield create_llm_chunk(MessageType.ERROR, f"Error: {str(e)}", provider='anthropic')
