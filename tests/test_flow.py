"""
Integration test for the full MCP serializer flow.
This test demonstrates the complete workflow from registration to request processing.
"""

import json
from mcp_serializer.registry import MCPRegistry
from mcp_serializer.initializer import Initializer
from mcp_serializer.serializers import JsonRpcSerializer
from mcp_serializer.features.tool.contents import ToolsContent
from mcp_serializer.features.resource.contents import ResourceContent
from mcp_serializer.features.prompt.contents import PromptsContent

# Initialize registry at module level
registry = MCPRegistry()

# ============================================================================
# Register Tools
# ============================================================================


@registry.tool()
def add_numbers(a: int, b: int):
    """Add two numbers and return the result."""
    result = a + b
    content = ToolsContent()
    content.add_text(f"The sum of {a} and {b} is {result}")
    return content


@registry.tool(name="echo")
def echo_message(message: str, uppercase: bool = False):
    """Echo tool

    Echo a message, optionally in uppercase."""
    output = message.upper() if uppercase else message
    content = ToolsContent()
    content.add_text(output)
    return content


@registry.tool()
def get_weather(city: str):
    """Get weather tool

    Get weather for a city."""
    content = ToolsContent()
    content.add_text(f"Weather in {city}: Sunny, 72°F")
    return content


# ============================================================================
# Register Resources
# ============================================================================


@registry.resource(uri="resource/config/")
def get_config(config_name: str):
    """
    Get config
    tool

    Get configuration file content."""
    content = ResourceContent()
    content.add_text_content(f"# Config: {config_name}\nkey=value", "text/plain")
    return content


@registry.resource(uri="resource/settings")
def get_settings(setting_name: str, setting_type):
    """
    Get settings tool

    Get settings file content."""
    content = ResourceContent()
    content.add_text_content(
        f"# Settings: {setting_name}\nkey=value\ntype={setting_type}", "text/plain"
    )
    return content


# Add static resource
readme_content = ResourceContent()
readme_content.add_text_content(
    "# MCP Serializer\nA library for MCP protocol serialization.", "text/markdown"
)
registry.add_resource(
    uri="file:///README.md",
    content=readme_content,
    name="readme",
    description="Project README file",
)


# Add JSON resource
api_docs_content = ResourceContent()
api_docs_content.add_text_content(
    json.dumps({"version": "1.0", "endpoints": ["/api/v1/tools", "/api/v1/resources"]}),
    "application/json",
)
registry.add_resource(
    uri="file:///api-docs.json",
    content=api_docs_content,
    name="api_docs",
    description="API documentation",
)

# add http resource
registry.add_resource(
    uri="https://example.com/api/data",
    name="api_data",
)


# ============================================================================
# Register Prompts
# ============================================================================


@registry.prompt()
def greeting_prompt():
    """Greeting prompt

    Generate a greeting prompt."""
    content = PromptsContent()
    content.add_text(
        "Hello! How can I assist you today?", role=PromptsContent.Roles.ASSISTANT
    )
    return content


@registry.prompt()
def code_review_prompt(language: str, code_snippet: str):
    """Code review prompt

    Generate a code review prompt with context."""
    content = PromptsContent()
    content.add_text(
        f"Please review the following {language} code:", role=PromptsContent.Roles.USER
    )
    content.add_text(code_snippet, role="user")
    content.add_text(
        "I'll review this code for best practices, potential bugs, and suggestions.",
        role="assistant",
    )
    return content


@registry.prompt(name="summarize", description="Summarize a document")
def summarize_prompt(document: str, max_length: int = 100):
    """Generate a summarization prompt."""
    content = PromptsContent()
    content.add_text(
        f"Please summarize the following document in under {max_length} words:",
        role="user",
    )
    content.add_text(document, role="user")
    return content


# ============================================================================
# Create Initializer and Serializer
# ============================================================================

initializer = Initializer(
    protocol_version="2024-11-05",
    instructions="This is a test MCP server with tools, resources, and prompts.",
)

# Add server info
initializer.add_server_info(
    name="test-mcp-server", version="1.0.0", title="Test MCP Server"
)

# Add capabilities
initializer.add_tools(list_changed=False)
initializer.add_resources(subscribe=False, list_changed=False)
initializer.add_prompt(list_changed=False)

# Create serializer
serializer = JsonRpcSerializer(initializer, registry)


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
    assert response["result"]["serverInfo"]["name"] == "test-mcp-server"
    assert "capabilities" in response["result"]
    assert "tools" in response["result"]["capabilities"]
    assert "resources" in response["result"]["capabilities"]
    assert "prompts" in response["result"]["capabilities"]


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


def test_resources_list_request():
    """Test listing available resources."""
    request = {"jsonrpc": "2.0", "id": 5, "method": "resources/list", "params": {}}

    response = serializer.process_request(request)

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 5
    assert "result" in response
    assert "resources" in response["result"]
    assert len(response["result"]["resources"]) == 3  # README and api-docs

    resource_names = [res["name"] for res in response["result"]["resources"]]
    assert "readme" in resource_names
    assert "api_docs" in resource_names
    assert "api_data" in resource_names

    resource_urls = [res["uri"] for res in response["result"]["resources"]]
    assert "file:///README.md" in resource_urls
    assert "file:///api-docs.json" in resource_urls
    assert "https://example.com/api/data" in resource_urls


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
        "params": {"uri": "file:///config/app"},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response
    assert "Config: app" in str(response["result"])


def test_prompts_list_request():
    """Test listing available prompts."""
    request = {"jsonrpc": "2.0", "id": 8, "method": "prompts/list", "params": {}}

    response = serializer.process_request(request)

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 8
    assert "result" in response
    assert "prompts" in response["result"]
    assert len(response["result"]["prompts"]) == 3  # greeting, code_review, summarize

    prompt_names = [prompt["name"] for prompt in response["result"]["prompts"]]
    assert "greeting" in prompt_names
    assert "code_review" in prompt_names
    assert "summarize" in prompt_names


def test_prompts_get_request():
    """Test getting a prompt."""
    # Test greeting prompt
    request = {
        "jsonrpc": "2.0",
        "id": 9,
        "method": "prompts/get",
        "params": {"name": "greeting"},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 9
    assert "result" in response
    assert "messages" in response["result"]
    assert "Hello" in str(response["result"]["messages"])

    # Test code review prompt with parameters
    request = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "prompts/get",
        "params": {
            "name": "code_review",
            "arguments": {
                "language": "Python",
                "code_snippet": "def hello():\n    print('world')",
            },
        },
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response
    assert "messages" in response["result"]
    assert "Python" in str(response["result"]["messages"])


def test_batch_request():
    """Test batch request processing."""
    batch_request = [
        {"jsonrpc": "2.0", "id": 11, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 12, "method": "resources/list", "params": {}},
        {"jsonrpc": "2.0", "id": 13, "method": "prompts/list", "params": {}},
    ]

    responses = serializer.process_request(batch_request)

    assert responses is not None
    assert isinstance(responses, list)
    assert len(responses) == 3
    assert all("result" in resp for resp in responses)


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
    assert response["error"]["code"] == -32002  # Tool not found

    # Test missing required parameter
    request = {
        "jsonrpc": "2.0",
        "id": 16,
        "method": "tools/call",
        "params": {
            "name": "calculator_add",
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
