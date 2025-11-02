"""
Integration test for MCP serializer tools flow.
This test demonstrates the complete workflow for tool registration and execution.
"""

import json
from pydantic import BaseModel
from mcp_serializer.registry import MCPRegistry
from mcp_serializer.initializer import MCPInitializer
from mcp_serializer.serializers import MCPSerializer
from mcp_serializer.features.tool.result import ToolsResult
from mcp_serializer.features.resource.schema import AnnotationSchema

# Initialize registry at module level
registry = MCPRegistry()


# ============================================================================
# Register Tools
# ============================================================================


@registry.tool()
def add_numbers(a: int, b: int):
    """Add two numbers and return the result."""
    result = a + b
    content = ToolsResult()
    return f"The sum of {a} and {b} is {result}"


@registry.tool(name="echo")
def echo_message(message: str, uppercase: bool = False):
    """Echo tool

    Echo a message, optionally in uppercase."""
    output = message.upper() if uppercase else message
    content = ToolsResult()
    content.add_text_content(output)
    return content


@registry.tool()
def get_weather(city: str):
    """Get weather tool

    Get weather for a city."""
    content = ToolsResult()
    return f"Weather in {city}: Sunny, 72°F"


# ============================================================================
# Create Initializer and Serializer
# ============================================================================

initializer = MCPInitializer(
    protocol_version="2024-11-05", instructions="This is a test MCP server with tools."
)

# Add server info
initializer.add_server_info(
    name="test-mcp-server-tools", version="1.0.0", title="Test MCP Server - Tools"
)

# Add capabilities
initializer.add_tools(list_changed=False)

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
    assert response["result"]["serverInfo"]["name"] == "test-mcp-server-tools"
    assert "capabilities" in response["result"]
    assert "tools" in response["result"]["capabilities"]


def test_tools_list_request():
    """Test listing available tools."""
    request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

    response = serializer.process_request(request)

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 2
    assert "result" in response
    assert "tools" in response["result"]
    assert len(response["result"]["tools"]) == 3

    tool_names = [tool["name"] for tool in response["result"]["tools"]]
    assert "add_numbers" in tool_names
    assert "echo" in tool_names
    assert "get_weather" in tool_names


def test_tools_call_request():
    """Test calling a tool."""
    # Test calculator add
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "add_numbers", "arguments": {"a": 10, "b": 20}},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 3
    assert "result" in response
    assert "content" in response["result"]
    assert "30" in str(response["result"]["content"])

    # Test echo with uppercase
    request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "echo",
            "arguments": {"message": "hello world", "uppercase": True},
        },
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response
    assert "HELLO WORLD" in str(response["result"]["content"])


def test_error_handling():
    """Test error handling for invalid requests."""
    # Test invalid method
    request = {"jsonrpc": "2.0", "id": 14, "method": "invalid/method", "params": {}}

    response = serializer.process_request(request)

    assert response is not None
    assert "error" in response
    assert response["error"]["code"] == -32601  # Method not found

    # Test tool not found
    request = {
        "jsonrpc": "2.0",
        "id": 15,
        "method": "tools/call",
        "params": {"name": "nonexistent_tool", "arguments": {}},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "error" in response
    assert response["error"]["code"] == -32002  # Tools not found

    # Test missing required parameter
    request = {
        "jsonrpc": "2.0",
        "id": 16,
        "method": "tools/call",
        "params": {
            "name": "add_numbers",
            "arguments": {"a": 10},  # Missing 'b'
        },
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "error" in response
    assert response["error"]["code"] == -32602  # Invalid params


def test_notification():
    """Test notification (request without id)."""
    request = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}

    response = serializer.process_request(request)

    # Notifications should not return a response
    assert response is None


def test_json_string_request():
    """Test request as JSON string."""
    request_str = json.dumps(
        {"jsonrpc": "2.0", "id": 17, "method": "tools/list", "params": {}}
    )

    response = serializer.process_request(request_str)

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 17
    assert "result" in response


def test_batch_request():
    """Test batch request processing with tools."""
    batch_request = [
        {"jsonrpc": "2.0", "id": 11, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {"name": "add_numbers", "arguments": {"a": 5, "b": 10}},
        },
    ]

    responses = serializer.process_request(batch_request)

    assert responses is not None
    assert isinstance(responses, list)
    assert len(responses) == 2
    assert all("result" in resp for resp in responses)
