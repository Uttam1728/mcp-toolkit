"""
Data Access Object for MCP configurations.
"""
import logging
from typing import List, Dict, Any, Optional, Type

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import MCPModel

# Set up logging
logger = logging.getLogger(__name__)


class BaseDao:
    """Base Data Access Object with common CRUD operations."""

    def __init__(self, session: AsyncSession, db_model: Type):
        """
        Initialize the DAO with a session and model.
        
        Args:
            session: SQLAlchemy async session
            db_model: SQLAlchemy model class
        """
        self.session = session
        self.db_model = db_model

    def add_object(self, **kwargs):
        """
        Create a new object with the given attributes.
        
        Args:
            **kwargs: Attributes for the new object
            
        Returns:
            The created object
        """
        obj = self.db_model(**kwargs)
        self.session.add(obj)
        return obj

    async def get_all(self):
        """
        Get all objects.
        
        Returns:
            List of all objects
        """
        query = select(self.db_model)
        result = await self.session.execute(query)
        return result.scalars().all()


class MCPDao(BaseDao):
    """Data Access Object for MCP model operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the MCP DAO with a session.
        
        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session=session, db_model=MCPModel)

    async def get_mcp_by_id(self, mcp_id: str) -> Optional[MCPModel]:
        """
        Get MCP record by ID.
        
        Args:
            mcp_id: ID of the MCP record
            
        Returns:
            The MCP record, or None if not found
        """
        try:
            query = select(MCPModel).where(MCPModel.id == mcp_id)
            result = await self.session.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting MCP record by ID {mcp_id}: {e}")
            raise

    async def get_mcps_by_user_id(self, user_id: str) -> List[MCPModel]:
        """
        Get all MCP records for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of MCP records for the user
        """
        try:
            query = select(MCPModel).where(MCPModel.user_id == user_id)
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting MCP records for user {user_id}: {e}")
            raise

    async def update_mcp(self, mcp_id: str, update_data: Dict[str, Any]):
        """
        Update MCP record.
        
        Args:
            mcp_id: ID of the MCP record
            update_data: Data to update
            
        Returns:
            Result of the update operation
        """
        try:
            query = update(MCPModel).where(MCPModel.id == mcp_id).values(**update_data)
            result = await self.session.execute(query)
            return result
        except Exception as e:
            logger.error(f"Error updating MCP record {mcp_id}: {e}")
            raise

    async def delete_mcp(self, mcp_id: str) -> bool:
        """
        Delete MCP record.
        
        Args:
            mcp_id: ID of the MCP record
            
        Returns:
            True if successful
        """
        try:
            query = delete(MCPModel).where(MCPModel.id == mcp_id)
            await self.session.execute(query)
            return True
        except Exception as e:
            logger.error(f"Error deleting MCP record {mcp_id}: {e}")
            raise

    async def toggle_inactive(self, mcp_id: str, inactive: bool):
        """
        Toggle inactive status.
        
        Args:
            mcp_id: ID of the MCP record
            inactive: New inactive status
            
        Returns:
            Result of the update operation
        """
        try:
            return await self.update_mcp(mcp_id, {"inactive": inactive})
        except Exception as e:
            logger.error(f"Error toggling inactive status for MCP record {mcp_id}: {e}")
            raise
