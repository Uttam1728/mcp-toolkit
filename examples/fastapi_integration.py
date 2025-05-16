"""
Example of integrating MCP with FastAPI.
"""
import logging
import uuid
from typing import List, Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from mcp_toolkit.configs import (
    MCPService,
    MCPRouter,
    MCPCreateRequest,
    MCPModelClass,
    UserData
)
from mcp_toolkit.configs.models import Base

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="MCP Toolkit Example")

# Database configuration
DATABASE_URL = "sqlite+aiosqlite:///./mcp_toolkit_example.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# Dependency for getting the database session
async def get_session() -> AsyncSession:
    """Get a database session."""
    async with async_session() as session:
        yield session


# Dependency for getting the current user (simplified for example)
async def get_current_user() -> UserData:
    """Get the current user (simplified for example)."""
    return UserData(user_id="example_user")


# Dependency for getting the MCP service
async def get_mcp_service(session: AsyncSession = Depends(get_session)) -> MCPService:
    """Get the MCP service."""
    return MCPService(session=session)


# Override the router dependencies
app.dependency_overrides = {
    "get_session": get_session,
    "get_current_user": get_current_user,
    "get_mcp_service": get_mcp_service
}

# Include the MCP router
app.include_router(MCPRouter)


# Add a custom endpoint for listing tools from all MCP servers
@app.get("/tools", response_model=List[Dict[str, Any]])
async def list_tools(mcp_service: MCPService = Depends(get_mcp_service)):
    """List all available tools from configured MCP servers."""
    try:
        # Get all active MCP servers
        mcps = await mcp_service.get_mcps_by_user(UserData(user_id="example_user"))
        active_mcps = [mcp for mcp in mcps if not mcp.inactive]
        
        # This would normally use the MCP client to list tools
        # For this example, we'll return dummy data
        tools = [
            {
                "name": f"tool_{i}",
                "description": f"Example tool {i} from {mcp.mcp_name}",
                "server": mcp.mcp_name
            }
            for i, mcp in enumerate(active_mcps)
        ]
        
        return tools
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Startup event to create tables
@app.on_event("startup")
async def startup():
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a default MCP server for testing
    async with async_session() as session:
        mcp_service = MCPService(session=session)
        try:
            await mcp_service.create_mcp(
                mcp_name="example_server",
                sse_url="https://example.com/mcp/example",
                user_data=UserData(user_id="example_user"),
                type="sse",
                source="example"
            )
            await session.commit()
            logger.info("Created default MCP server")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating default MCP server: {e}")


# Shutdown event to close the database
@app.on_event("shutdown")
async def shutdown():
    """Close database connection on shutdown."""
    await engine.dispose()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
