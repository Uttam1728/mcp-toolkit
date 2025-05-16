"""
Database models for MCP configurations.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps to models."""

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MCPModel(TimestampMixin, Base):
    """
    MCP (Model-Controller-Persistence) model for CRUD operations.

    Properties:
    - id: UUID primary key
    - mcp_name: Name of the MCP
    - sse_url: URL for Server-Sent Events
    - user_id: User ID from UserData
    - inactive: Boolean switch for inactive status
    - type: Type of MCP server
    - command: Command to run the server
    - args: Arguments for the command (stored as JSON)
    - env_vars: Environment variables (stored as JSON)
    - source: Origin of the MCP configuration (e.g., 'vscode', 'website')
    - created_at: Timestamp for creation (from TimestampMixin)
    - updated_at: Timestamp for updates (from TimestampMixin)
    """
    __tablename__ = "mcp_model"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mcp_name = Column(String, nullable=False)
    sse_url = Column(String, nullable=True)
    user_id = Column(String, nullable=False)
    inactive = Column(Boolean, default=False)
    type = Column(String, nullable=False)
    command = Column(String, nullable=True)
    args = Column(JSON, nullable=True)
    env_vars = Column(JSON, nullable=True)
    source = Column(String, nullable=True)

    def __repr__(self):
        return f"<MCPModel(id={self.id}, name={self.mcp_name}, type={self.type})>"
