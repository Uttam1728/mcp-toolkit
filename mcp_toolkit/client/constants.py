"""
Constants for MCP client.
"""
import datetime
import uuid
from typing import List, Dict, Any, Optional

# Message types for streaming
class MessageType:
    """Message types for streaming responses."""
    DATA = "data"
    PROGRESS = "progress"
    ERROR = "error"
    STREAM_START = "stream_start"
    STREAM_END = "stream_end"
    CONVERSATION_TITLE = "conversation_title"
    LAST_AI_MESSAGE = "last_ai_message"


# Default MCP server model
class MCPServerModel:
    """Model class for MCP server configuration."""
    
    def __init__(
        self,
        id: uuid.UUID,
        mcp_name: str,
        sse_url: str,
        user_id: str = "system",
        inactive: bool = False,
        type: str = "sse",
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        source: str = "system",
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None
    ):
        """
        Initialize an MCP server model.
        
        Args:
            id: UUID for the server
            mcp_name: Name of the MCP server
            sse_url: URL for SSE connection
            user_id: User ID that owns this server
            inactive: Whether the server is inactive
            type: Type of server (sse or stdio)
            command: Command to run for stdio servers
            args: Arguments for the command
            env_vars: Environment variables for the command
            source: Source of the server configuration
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.mcp_name = mcp_name
        self.sse_url = sse_url
        self.user_id = user_id
        self.inactive = inactive
        self.type = type
        self.command = command
        self.args = args
        self.env_vars = env_vars
        self.source = source
        self.created_at = created_at or datetime.datetime.now()
        self.updated_at = updated_at or datetime.datetime.now()


# Default SSE servers configuration
BUILTIN_MCP_SERVERS = [
    MCPServerModel(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        mcp_name="web_search",
        sse_url="https://example.com/mcp/web_search",
        user_id="system",
        inactive=False,
        type="sse",
        source="system",
    ),
]
