"""
Tests for the MCP configs module.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_toolkit.configs import (
    MCPService,
    MCPModel,
    MCPCreateRequest,
    MCPUpdateRequest,
)
from mcp_toolkit.configs.exceptions import MCPUnauthorizedException
from mcp_toolkit.configs.service import UserData


@pytest.fixture
def user_data():
    """Create test user data."""
    return UserData(user_id="test_user")


@pytest.fixture
def mcp_model():
    """Create a test MCP model."""
    return MCPModel(
        id=uuid.uuid4(),
        mcp_name="test_server",
        sse_url="https://example.com/mcp/test",
        user_id="test_user",
        inactive=False,
        type="sse",
        source="test",
    )


@pytest.fixture
def mcp_create_request():
    """Create a test MCP create request."""
    return MCPCreateRequest(
        mcp_name="test_server",
        sse_url="https://example.com/mcp/test",
        type="sse",
        source="test",
    )


@pytest.fixture
def mcp_update_request():
    """Create a test MCP update request."""
    return MCPUpdateRequest(
        mcp_name="updated_server",
        sse_url="https://example.com/mcp/updated",
    )


@pytest.mark.asyncio
async def test_mcp_service_create_mcp(user_data, mcp_create_request):
    """Test MCP service create_mcp method."""
    # Create mock session and DAO
    mock_session = AsyncMock(spec=AsyncSession)
    mock_dao = AsyncMock()

    # Set up mock add_object method
    mock_mcp = MagicMock(spec=MCPModel)
    mock_dao.add_object.return_value = mock_mcp

    # Create service with mocked DAO
    with patch('mcp_toolkit.configs.service.MCPDao', return_value=mock_dao):
        service = MCPService(session=mock_session)

        # Call create_mcp
        result = await service.create_mcp(
            mcp_name=mcp_create_request.mcp_name,
            sse_url=mcp_create_request.sse_url,
            user_data=user_data,
            type=mcp_create_request.type,
            source=mcp_create_request.source,
        )

        # Check that add_object was called with the correct arguments
        mock_dao.add_object.assert_called_once_with(
            mcp_name=mcp_create_request.mcp_name,
            sse_url=mcp_create_request.sse_url,
            user_id=user_data.userId,
            inactive=False,
            type=mcp_create_request.type,
            command=None,
            args=None,
            env_vars=None,
            source=mcp_create_request.source,
        )

        # Check that commit was called
        mock_session.commit.assert_called_once()

        # Check that the result is the mock MCP
        assert result == mock_mcp


@pytest.mark.asyncio
async def test_mcp_service_get_mcp_by_id(user_data, mcp_model):
    """Test MCP service get_mcp_by_id method."""
    # Create mock session and DAO
    mock_session = AsyncMock(spec=AsyncSession)
    mock_dao = AsyncMock()

    # Set up mock get_mcp_by_id method
    mock_dao.get_mcp_by_id.return_value = mcp_model

    # Create service with mocked DAO
    with patch('mcp_toolkit.configs.service.MCPDao', return_value=mock_dao):
        service = MCPService(session=mock_session)

        # Call get_mcp_by_id
        result = await service.get_mcp_by_id(str(mcp_model.id), user_data)

        # Check that get_mcp_by_id was called with the correct arguments
        mock_dao.get_mcp_by_id.assert_called_once_with(str(mcp_model.id))

        # Check that the result is the mock MCP
        assert result == mcp_model


@pytest.mark.asyncio
async def test_mcp_service_get_mcp_by_id_not_found(user_data):
    """Test MCP service get_mcp_by_id method when the MCP is not found."""
    # Create mock session and DAO
    mock_session = AsyncMock(spec=AsyncSession)
    mock_dao = AsyncMock()

    # Set up mock get_mcp_by_id method to return None
    mock_dao.get_mcp_by_id.return_value = None

    # Create service with mocked DAO
    with patch('mcp_toolkit.configs.service.MCPDao', return_value=mock_dao):
        service = MCPService(session=mock_session)

        # Call get_mcp_by_id
        result = await service.get_mcp_by_id("nonexistent_id", user_data)

        # Check that get_mcp_by_id was called with the correct arguments
        mock_dao.get_mcp_by_id.assert_called_once_with("nonexistent_id")

        # Check that the result is None
        assert result is None


@pytest.mark.asyncio
async def test_mcp_service_get_mcp_by_id_unauthorized(user_data, mcp_model):
    """Test MCP service get_mcp_by_id method when the user is not authorized."""
    # Create mock session and DAO
    mock_session = AsyncMock(spec=AsyncSession)
    mock_dao = AsyncMock()

    # Set up mock get_mcp_by_id method
    mcp_model.user_id = "other_user"  # Different user
    mock_dao.get_mcp_by_id.return_value = mcp_model

    # Create service with mocked DAO
    with patch('mcp_toolkit.configs.service.MCPDao', return_value=mock_dao):
        service = MCPService(session=mock_session)

        # Call get_mcp_by_id and expect an exception
        with pytest.raises(MCPUnauthorizedException):
            await service.get_mcp_by_id(str(mcp_model.id), user_data)

        # Check that get_mcp_by_id was called with the correct arguments
        mock_dao.get_mcp_by_id.assert_called_once_with(str(mcp_model.id))


@pytest.mark.asyncio
async def test_mcp_service_get_mcps_by_user(user_data, mcp_model):
    """Test MCP service get_mcps_by_user method."""
    # Create mock session and DAO
    mock_session = AsyncMock(spec=AsyncSession)
    mock_dao = AsyncMock()

    # Set up mock get_mcps_by_user_id method
    mock_dao.get_mcps_by_user_id.return_value = [mcp_model]

    # Create service with mocked DAO
    with patch('mcp_toolkit.configs.service.MCPDao', return_value=mock_dao):
        service = MCPService(session=mock_session)

        # Call get_mcps_by_user
        result = await service.get_mcps_by_user(user_data)

        # Check that get_mcps_by_user_id was called with the correct arguments
        mock_dao.get_mcps_by_user_id.assert_called_once_with(user_data.userId)

        # Check that the result is the list of mock MCPs
        assert result == [mcp_model]


@pytest.mark.asyncio
async def test_mcp_service_update_mcp(user_data, mcp_model, mcp_update_request):
    """Test MCP service update_mcp method."""
    # Create mock session and DAO
    mock_session = AsyncMock(spec=AsyncSession)
    mock_dao = AsyncMock()

    # Set up mock methods
    mock_dao.get_mcp_by_id.return_value = mcp_model
    mock_dao.update_mcp.return_value = None

    # Create updated MCP model
    updated_mcp = MagicMock(spec=MCPModel)
    updated_mcp.mcp_name = mcp_update_request.mcp_name
    updated_mcp.sse_url = mcp_update_request.sse_url

    # Set up mock get_mcp_by_id to return the updated MCP on second call
    mock_dao.get_mcp_by_id.side_effect = [mcp_model, updated_mcp]

    # Create service with mocked DAO
    with patch('mcp_toolkit.configs.service.MCPDao', return_value=mock_dao):
        service = MCPService(session=mock_session)

        # Call update_mcp
        result = await service.update_mcp(
            str(mcp_model.id),
            mcp_update_request.model_dump(exclude_unset=True),
            user_data
        )

        # Check that get_mcp_by_id was called with the correct arguments
        mock_dao.get_mcp_by_id.assert_called_with(str(mcp_model.id))

        # Check that update_mcp was called with the correct arguments
        mock_dao.update_mcp.assert_called_once_with(
            str(mcp_model.id),
            mcp_update_request.model_dump(exclude_unset=True)
        )

        # Check that commit was called
        mock_session.commit.assert_called_once()

        # Check that the result is the updated MCP
        assert result == updated_mcp


@pytest.mark.asyncio
async def test_mcp_service_delete_mcp(user_data, mcp_model):
    """Test MCP service delete_mcp method."""
    # Create mock session and DAO
    mock_session = AsyncMock(spec=AsyncSession)
    mock_dao = AsyncMock()

    # Set up mock methods
    mock_dao.get_mcp_by_id.return_value = mcp_model
    mock_dao.delete_mcp.return_value = True

    # Create service with mocked DAO
    with patch('mcp_toolkit.configs.service.MCPDao', return_value=mock_dao):
        service = MCPService(session=mock_session)

        # Call delete_mcp
        result = await service.delete_mcp(str(mcp_model.id), user_data)

        # Check that get_mcp_by_id was called with the correct arguments
        mock_dao.get_mcp_by_id.assert_called_once_with(str(mcp_model.id))

        # Check that delete_mcp was called with the correct arguments
        mock_dao.delete_mcp.assert_called_once_with(str(mcp_model.id))

        # Check that commit was called
        mock_session.commit.assert_called_once()

        # Check that the result is True
        assert result is True
