import logging
import os

LOGGER_NAME = os.environ.get("MCP_LOGGER_NAME", "mcp")


def get_logger():
    """Get the current MCP logger instance."""
    return logging.getLogger(LOGGER_NAME)
