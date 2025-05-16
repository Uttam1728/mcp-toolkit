"""
Stream handling for MCP client responses.
"""
from typing import AsyncIterator, TypeVar, Generic, Callable, Awaitable, Any

T = TypeVar('T')


class CustomAsyncStream(Generic[T]):
    """
    A custom implementation of AsyncStream that wraps an async generator.
    
    This class provides a way to stream responses from MCP tools in a way
    that's compatible with LLM providers' streaming interfaces.
    """

    def __init__(self, generator_func: Callable[[], Awaitable[Any]]):
        """
        Initialize the stream with a generator function.
        
        Args:
            generator_func: An async generator function that yields chunks
        """
        self._generator = generator_func()

    def __aiter__(self) -> AsyncIterator[T]:
        """Return the async iterator."""
        return self

    async def __anext__(self) -> T:
        """Get the next item from the stream."""
        try:
            return await self._generator.__anext__()
        except StopAsyncIteration:
            raise
        except IndexError as e:
            # Convert IndexError to a proper exception instead of trying to call send() on it
            raise RuntimeError(f"Index error in async stream: {str(e)}")
