"""
Integration test for MCP serializer resources flow.
This test demonstrates the complete workflow for resource registration and access.
"""

import json
import tempfile
import os
from mcp_serializer.registry import MCPRegistry
from mcp_serializer.initializer import Initializer
from mcp_serializer.serializers import MCPSerializer
from mcp_serializer.features.resource.result import ResourceResult

# Initialize registry at module level
registry = MCPRegistry()


# ============================================================================
# Register Resources
# ============================================================================


# resource template
@registry.resource(uri="resource/config/")
def get_config(config_name: str):
    """
    Get config
    tool

    Get configuration file content."""
    content = ResourceResult()
    content.add_text_content(f"# Config: {config_name}\nkey=value", "text/plain")
    return content


# resource template
@registry.resource(uri="resource/settings")
def get_settings(setting_name: str, setting_type):
    """
    Get settings tool

    Get settings file content."""
    content = ResourceResult()
    content.add_text_content(
        f"# Settings: {setting_name}\nkey=value\ntype={setting_type}", "text/plain"
    )
    return content


# resource
@registry.resource(uri="file:///style")
def get_style():
    content = ResourceResult()
    content.add_text_content("body { background-color: #f0f0f0; }", "text/css")
    return content


# resource - using container directly
readme_content = ResourceResult()
readme_content.add_text_content(
    "# MCP Serializer\nA library for MCP protocol serialization.", "text/markdown"
)
registry._get_resource_container().add_resource(
    uri="file:///README.md",
    result=readme_content,
    name="readme",
    description="Project README file",
)

# resource
registry.add_http_resource(
    uri="https://example.com/api/data",
    name="api_data",
)

# resource from file
# Create a temporary JSON file for testing
temp_file = tempfile.NamedTemporaryFile(
    mode="w", suffix=".json", delete=False, dir=tempfile.gettempdir()
)
temp_file.write(json.dumps({"test": "data", "version": "1.0"}))
temp_file_path = temp_file.name
temp_file.close()

registry.add_file_resource(
    file=temp_file_path,
    title="Test JSON File",
    description="A test JSON file resource",
)


# ============================================================================
# Create Initializer and Serializer
# ============================================================================

initializer = Initializer(
    protocol_version="2024-11-05",
    instructions="This is a test MCP server with resources.",
)

# Add server info
initializer.add_server_info(
    name="test-mcp-server-resources",
    version="1.0.0",
    title="Test MCP Server - Resources",
)

# Add capabilities
initializer.add_resources(subscribe=False, list_changed=False)

# Create serializer
serializer = MCPSerializer(initializer, registry)


# ============================================================================
# Test Functions
# ============================================================================


def test_initialize_request():
    """Test the initialize request."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }

    response = serializer.process_request(request)

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response
    assert response["result"]["protocolVersion"] == "2024-11-05"
    assert "serverInfo" in response["result"]
    assert response["result"]["serverInfo"]["name"] == "test-mcp-server-resources"
    assert "capabilities" in response["result"]
    assert "resources" in response["result"]["capabilities"]


def test_resources_list_request():
    """Test listing available resources."""
    request = {"jsonrpc": "2.0", "id": 5, "method": "resources/list", "params": {}}

    response = serializer.process_request(request)

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 5
    assert "result" in response
    assert "resources" in response["result"]
    assert (
        len(response["result"]["resources"]) == 4
    )  # README, api_data, get_style and temp file

    resource_names = [res["name"] for res in response["result"]["resources"]]
    assert "readme" in resource_names
    assert "api_data" in resource_names
    assert "get_style" in resource_names

    resource_urls = [res["uri"] for res in response["result"]["resources"]]
    assert "file:///README.md" in resource_urls
    assert "https://example.com/api/data" in resource_urls
    # Temp file URI will be file://<temp_path>
    assert any("file://" in uri and ".json" in uri for uri in resource_urls)


def test_resource_template_list_request():
    """Test listing available resource templates."""
    request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "resources/templates/list",
        "params": {},
    }
    response = serializer.process_request(request)

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 6
    assert "result" in response
    assert "resourceTemplates" in response["result"]
    assert len(response["result"]["resourceTemplates"]) == 2
    resource_template_urls = [
        res["uri"] for res in response["result"]["resourceTemplates"]
    ]
    assert r"resource/config/{config_name}" in resource_template_urls
    assert r"resource/settings/{setting_name}/{setting_type}" in resource_template_urls


def test_resources_read_request():
    """Test reading a resource."""
    # Test reading README
    request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "resources/read",
        "params": {"uri": "file:///README.md"},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 6
    assert "result" in response
    assert "contents" in response["result"]
    assert "MCP Serializer" in str(response["result"])

    # Test reading template resource with parameters
    request = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "resources/read",
        "params": {"uri": "resource/config/app"},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response
    assert "Config: app" in str(response["result"])


def test_file_resource():
    """Test reading a file-based resource."""
    # Get the URI for the temp file from the registry
    resource_list = (
        serializer.registry.resource_container.schema_assembler.resource_list
    )
    temp_resource = None
    for resource in resource_list:
        if resource.uri.startswith("file://") and ".json" in resource.uri:
            if "README" not in resource.uri and "api-docs" not in resource.uri:
                temp_resource = resource
                break

    assert temp_resource is not None

    request = {
        "jsonrpc": "2.0",
        "id": 15,
        "method": "resources/read",
        "params": {"uri": temp_resource.uri},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response
    assert "contents" in response["result"]
    assert len(response["result"]["contents"]) == 1
    content = response["result"]["contents"][0]
    assert content["mimeType"] == "application/json"
    assert '"test": "data"' in content["text"]


def test_batch_request():
    """Test batch request processing with resources."""
    batch_request = [
        {"jsonrpc": "2.0", "id": 11, "method": "resources/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "resources/templates/list",
            "params": {},
        },
    ]

    responses = serializer.process_request(batch_request)

    assert responses is not None
    assert isinstance(responses, list)
    assert len(responses) == 2
    assert all("result" in resp for resp in responses)


def test_cleanup():
    """Clean up temporary files."""
    # Clean up the temp file
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)
