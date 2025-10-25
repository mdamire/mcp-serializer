"""
Integration test for MCP serializer prompts flow.
This test demonstrates the complete workflow for prompt registration and retrieval.
"""

import json
from mcp_serializer.registry import MCPRegistry
from mcp_serializer.initializer import Initializer
from mcp_serializer.serializers import JsonRpcSerializer
from mcp_serializer.features.prompt.result import PromptsResult, PromptsContent

# Initialize registry at module level
registry = MCPRegistry()

# ============================================================================
# As in Documentation
# ============================================================================

# registry.add_prompt_from_file(
#     "file.txt", role=PromptsResult.Roles.USER
# )  # this will be text content


# for complex cases you can return a PromptsResult object
# the function can be with optional/required arguments
@registry.prompt()
def greeting_prompt(type: str = "text"):
    """Greeting prompt

    Generate a greeting prompt."""
    result = PromptsResult()
    result.add_text(
        "Hello! How can I assist you today?", role=PromptsResult.Roles.ASSISTANT
    )
    result.add_file(
        "file.txt",
        role=PromptsResult.Roles.USER,
        title="File Title",
        description="File Description",
    )  # this will be embadded resource
    return result


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
    instructions="This is a test MCP server with prompts.",
)

# Add server info
initializer.add_server_info(
    name="test-mcp-server-prompts", version="1.0.0", title="Test MCP Server - Prompts"
)

# Add capabilities
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
    assert response["result"]["serverInfo"]["name"] == "test-mcp-server-prompts"
    assert "capabilities" in response["result"]
    assert "prompts" in response["result"]["capabilities"]


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
    """Test batch request processing with prompts."""
    batch_request = [
        {"jsonrpc": "2.0", "id": 11, "method": "prompts/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "prompts/get",
            "params": {"name": "greeting"},
        },
    ]

    responses = serializer.process_request(batch_request)

    assert responses is not None
    assert isinstance(responses, list)
    assert len(responses) == 2
    assert all("result" in resp for resp in responses)
