"""
Exceptions for MCP configurations.
"""


class MCPException(Exception):
    """Base exception for MCP module."""
    error_code = 5100
    message = "An error occurred in the MCP module."

    def __init__(self, message=None):
        self.message = message or self.message
        super().__init__(self.message)


class MCPCreationException(MCPException):
    """Exception raised when creating an MCP record fails."""
    error_code = 5101
    message = "Failed to create MCP record."


class MCPNotFoundException(MCPException):
    """Exception raised when an MCP record is not found."""
    error_code = 5102
    message = "MCP record not found."


class MCPUpdateException(MCPException):
    """Exception raised when updating an MCP record fails."""
    error_code = 5103
    message = "Failed to update MCP record."


class MCPDeletionException(MCPException):
    """Exception raised when deleting an MCP record fails."""
    error_code = 5104
    message = "Failed to delete MCP record."


class MCPToggleInactiveException(MCPException):
    """Exception raised when toggling inactive status fails."""
    error_code = 5105
    message = "Failed to toggle inactive status."


class MCPUnauthorizedException(MCPException):
    """Exception raised when a user is not authorized to access an MCP record."""
    error_code = 5106
    message = "Unauthorized access to MCP record."
