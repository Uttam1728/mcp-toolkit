"""
Service for MCP configurations.
"""
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .dao import MCPDao
from .exceptions import (
    MCPNotFoundException,
    MCPUnauthorizedException,
    MCPCreationException,
    MCPUpdateException,
    MCPDeletionException,
    MCPToggleInactiveException
)
from .models import MCPModel

# Set up logging
logger = logging.getLogger(__name__)


class UserData:
    """Simple user data class for authorization."""

    def __init__(self, user_id: str):
        """
        Initialize user data.
        
        Args:
            user_id: ID of the user
        """
        self.userId = user_id


class MCPService:
    """Service for MCP operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the MCP service.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.mcp_dao = MCPDao(session=self.session)

    async def create_mcp(self, mcp_name: str, sse_url: str, user_data: UserData,
                         inactive: bool = False, type: str = None, command: str = None,
                         args: List[str] = None, env_vars: Dict[str, str] = None, source: str = None) -> MCPModel:
        """
        Create a new MCP record.
        
        Args:
            mcp_name: Name of the MCP
            sse_url: URL for Server-Sent Events
            user_data: User data for authorization
            inactive: Whether the MCP is inactive
            type: Type of MCP server
            command: Command to run the server
            args: Arguments for the command
            env_vars: Environment variables
            source: Origin of the MCP configuration
            
        Returns:
            The created MCP record
            
        Raises:
            MCPCreationException: If creation fails
        """
        try:
            user_id = str(user_data.userId)
            mcp = self.mcp_dao.add_object(
                mcp_name=mcp_name,
                sse_url=sse_url,
                user_id=user_id,
                inactive=inactive,
                type=type,
                command=command,
                args=args,
                env_vars=env_vars,
                source=source
            )
            await self.session.commit()
            return mcp
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error in create_mcp service: {e}")
            raise MCPCreationException() from e

    async def get_mcp_by_id(self, mcp_id: str, user_data: Optional[UserData] = None) -> Optional[MCPModel]:
        """
        Get MCP record by ID.
        
        Args:
            mcp_id: ID of the MCP record
            user_data: User data for authorization check (optional)
            
        Returns:
            The MCP record, or None if not found
            
        Raises:
            MCPUnauthorizedException: If the user is not authorized to access the record
        """
        try:
            mcp = await self.mcp_dao.get_mcp_by_id(mcp_id)
            if not mcp:
                return None

            # If user_data is provided, we're doing an ownership check
            if user_data and mcp.user_id != str(user_data.userId):
                logger.warning(
                    f"User {user_data.userId} attempted to access MCP record {mcp_id} belonging to user {mcp.user_id}")
                raise MCPUnauthorizedException()

            return mcp
        except MCPUnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"Error in get_mcp_by_id service: {e}")
            raise

    async def get_mcps_by_user(self, user_data: UserData) -> List[MCPModel]:
        """
        Get all MCP records for a user.
        
        Args:
            user_data: User data for filtering
            
        Returns:
            List of MCP records for the user
        """
        try:
            user_id = str(user_data.userId)
            mcps = await self.mcp_dao.get_mcps_by_user_id(user_id)
            return mcps
        except Exception as e:
            logger.error(f"Error in get_mcps_by_user service: {e}")
            raise

    async def update_mcp(self, mcp_id: str, update_data: Dict[str, Any], user_data: UserData) -> MCPModel:
        """
        Update MCP record.
        
        Args:
            mcp_id: ID of the MCP record
            update_data: Data to update
            user_data: User data for authorization
            
        Returns:
            The updated MCP record
            
        Raises:
            MCPNotFoundException: If the record is not found
            MCPUnauthorizedException: If the user is not authorized to update the record
            MCPUpdateException: If the update fails
        """
        try:
            # Get the MCP record - ownership will be checked
            existing_mcp = await self.get_mcp_by_id(mcp_id, user_data)
            if not existing_mcp:
                logger.warning(f"MCP record {mcp_id} not found")
                raise MCPNotFoundException()

            # Update the record
            await self.mcp_dao.update_mcp(mcp_id, update_data)
            await self.session.commit()

            # Get the updated record
            updated_mcp = await self.mcp_dao.get_mcp_by_id(mcp_id)
            return updated_mcp
        except (MCPNotFoundException, MCPUnauthorizedException):
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error in update_mcp service: {e}")
            raise MCPUpdateException() from e

    async def delete_mcp(self, mcp_id: str, user_data: UserData) -> bool:
        """
        Delete MCP record.
        
        Args:
            mcp_id: ID of the MCP record
            user_data: User data for authorization
            
        Returns:
            True if successful
            
        Raises:
            MCPNotFoundException: If the record is not found
            MCPUnauthorizedException: If the user is not authorized to delete the record
            MCPDeletionException: If the deletion fails
        """
        try:
            # Get the MCP record - ownership will be checked
            existing_mcp = await self.get_mcp_by_id(mcp_id, user_data)
            if not existing_mcp:
                logger.warning(f"MCP record {mcp_id} not found")
                raise MCPNotFoundException()

            # Delete the record
            result = await self.mcp_dao.delete_mcp(mcp_id)
            await self.session.commit()
            return result
        except (MCPNotFoundException, MCPUnauthorizedException):
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error in delete_mcp service: {e}")
            raise MCPDeletionException() from e

    async def toggle_inactive(self, mcp_id: str, inactive: bool, user_data: UserData) -> MCPModel:
        """
        Toggle inactive status.
        
        Args:
            mcp_id: ID of the MCP record
            inactive: New inactive status
            user_data: User data for authorization
            
        Returns:
            The updated MCP record
            
        Raises:
            MCPNotFoundException: If the record is not found
            MCPUnauthorizedException: If the user is not authorized to update the record
            MCPToggleInactiveException: If the toggle fails
        """
        try:
            # Get the MCP record - ownership will be checked
            existing_mcp = await self.get_mcp_by_id(mcp_id, user_data)
            if not existing_mcp:
                logger.warning(f"MCP record {mcp_id} not found")
                raise MCPNotFoundException()

            # Toggle inactive status
            await self.mcp_dao.toggle_inactive(mcp_id, inactive)
            await self.session.commit()

            # Get the updated record
            updated_mcp = await self.mcp_dao.get_mcp_by_id(mcp_id)
            return updated_mcp
        except (MCPNotFoundException, MCPUnauthorizedException):
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error in toggle_inactive service: {e}")
            raise MCPToggleInactiveException() from e
