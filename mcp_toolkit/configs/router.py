"""
FastAPI router for MCP configurations.
"""
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import (
    MCPNotFoundException,
    MCPUnauthorizedException,
    MCPCreationException,
    MCPUpdateException,
    MCPDeletionException,
    MCPToggleInactiveException
)
from .serializers import (
    MCPCreateRequest,
    MCPUpdateRequest,
    MCPToggleInactiveRequest,
    MCPModelClass,
    MCPListResponse
)
from .service import MCPService, UserData

# Set up logging
logger = logging.getLogger(__name__)

# Create router
MCPRouter = APIRouter(prefix="/mcp", tags=["MCP"])


# Dependency for getting the database session
async def get_session() -> AsyncSession:
    """
    Get a database session.
    
    This is a placeholder that should be replaced with your actual session management.
    
    Returns:
        An async SQLAlchemy session
    """
    # This should be replaced with your actual session management
    raise NotImplementedError("You must implement the get_session dependency")


# Dependency for getting the current user
async def get_current_user() -> UserData:
    """
    Get the current user.
    
    This is a placeholder that should be replaced with your actual user management.
    
    Returns:
        User data for the current user
    """
    # This should be replaced with your actual user management
    raise NotImplementedError("You must implement the get_current_user dependency")


# Dependency for getting the MCP service
async def get_mcp_service(session: AsyncSession = Depends(get_session)) -> MCPService:
    """
    Get the MCP service.
    
    Args:
        session: SQLAlchemy async session
        
    Returns:
        MCP service instance
    """
    return MCPService(session=session)


# Create MCP record
@MCPRouter.post("/configs", response_model=MCPModelClass, status_code=201)
async def create_mcp(
    request: MCPCreateRequest,
    user: UserData = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """
    Create a new MCP record.
    
    Args:
        request: MCP creation request
        user: Current user
        mcp_service: MCP service
        
    Returns:
        The created MCP record
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        result = await mcp_service.create_mcp(
            mcp_name=request.mcp_name,
            sse_url=request.sse_url,
            user_data=user,
            inactive=request.inactive,
            type=request.type,
            command=request.command,
            args=request.args,
            env_vars=request.env_vars,
            source=request.source
        )
        return MCPModelClass.model_validate(result)
    except MCPCreationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating MCP record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Get MCP record by ID
@MCPRouter.get("/configs/{mcp_id}", response_model=MCPModelClass)
async def get_mcp_by_id(
    mcp_id: str = Path(..., description="ID of the MCP record"),
    user: UserData = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """
    Get MCP record by ID.
    
    Args:
        mcp_id: ID of the MCP record
        user: Current user
        mcp_service: MCP service
        
    Returns:
        The MCP record
        
    Raises:
        HTTPException: If the record is not found or the user is not authorized
    """
    try:
        result = await mcp_service.get_mcp_by_id(mcp_id, user)
        if not result:
            raise HTTPException(status_code=404, detail="MCP record not found")
        return MCPModelClass.model_validate(result)
    except MCPUnauthorizedException:
        raise HTTPException(status_code=403, detail="Unauthorized access to this MCP record")
    except Exception as e:
        logger.error(f"Error getting MCP record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Get all MCP records for a user
@MCPRouter.get("/configs", response_model=MCPListResponse)
async def get_mcps_by_user(
    user: UserData = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """
    Get all MCP records for a user.
    
    Args:
        user: Current user
        mcp_service: MCP service
        
    Returns:
        List of MCP records for the user
        
    Raises:
        HTTPException: If an error occurs
    """
    try:
        results = await mcp_service.get_mcps_by_user(user)
        return MCPListResponse(
            items=[MCPModelClass.model_validate(result) for result in results],
            count=len(results)
        )
    except Exception as e:
        logger.error(f"Error getting MCP records: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Update MCP record
@MCPRouter.put("/configs/{mcp_id}", response_model=MCPModelClass)
async def update_mcp(
    request: MCPUpdateRequest,
    mcp_id: str = Path(..., description="ID of the MCP record"),
    user: UserData = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """
    Update MCP record.
    
    Args:
        request: MCP update request
        mcp_id: ID of the MCP record
        user: Current user
        mcp_service: MCP service
        
    Returns:
        The updated MCP record
        
    Raises:
        HTTPException: If the record is not found, the user is not authorized, or the update fails
    """
    try:
        # Filter out None values
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}
        result = await mcp_service.update_mcp(mcp_id, update_data, user)
        return MCPModelClass.model_validate(result)
    except MCPNotFoundException:
        raise HTTPException(status_code=404, detail="MCP record not found")
    except MCPUnauthorizedException:
        raise HTTPException(status_code=403, detail="Unauthorized access to this MCP record")
    except MCPUpdateException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating MCP record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Delete MCP record
@MCPRouter.delete("/configs/{mcp_id}", status_code=204)
async def delete_mcp(
    mcp_id: str = Path(..., description="ID of the MCP record"),
    user: UserData = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """
    Delete MCP record.
    
    Args:
        mcp_id: ID of the MCP record
        user: Current user
        mcp_service: MCP service
        
    Raises:
        HTTPException: If the record is not found, the user is not authorized, or the deletion fails
    """
    try:
        await mcp_service.delete_mcp(mcp_id, user)
    except MCPNotFoundException:
        raise HTTPException(status_code=404, detail="MCP record not found")
    except MCPUnauthorizedException:
        raise HTTPException(status_code=403, detail="Unauthorized access to this MCP record")
    except MCPDeletionException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting MCP record: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Toggle inactive status
@MCPRouter.patch("/configs/{mcp_id}/toggle-inactive", response_model=MCPModelClass)
async def toggle_inactive(
    request: MCPToggleInactiveRequest,
    mcp_id: str = Path(..., description="ID of the MCP record"),
    user: UserData = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """
    Toggle inactive status.
    
    Args:
        request: Toggle inactive request
        mcp_id: ID of the MCP record
        user: Current user
        mcp_service: MCP service
        
    Returns:
        The updated MCP record
        
    Raises:
        HTTPException: If the record is not found, the user is not authorized, or the toggle fails
    """
    try:
        result = await mcp_service.toggle_inactive(mcp_id, request.inactive, user)
        return MCPModelClass.model_validate(result)
    except MCPNotFoundException:
        raise HTTPException(status_code=404, detail="MCP record not found")
    except MCPUnauthorizedException:
        raise HTTPException(status_code=403, detail="Unauthorized access to this MCP record")
    except MCPToggleInactiveException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error toggling inactive status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
