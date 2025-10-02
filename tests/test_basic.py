"""Basic tests for mcp-serializer package."""

import pytest

from mcp_serializer import __version__


def test_version():
    """Test that version is set correctly."""
    assert __version__ == "0.1.0"


def test_package_import():
    """Test that package can be imported."""
    import mcp_serializer

    assert mcp_serializer is not None
