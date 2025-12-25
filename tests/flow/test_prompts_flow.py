"""
Integration test for MCP serializer prompts flow.
This test demonstrates the complete workflow for prompt registration and retrieval.
"""

import json
import tempfile
import os
from mcp_serializer.registry import MCPRegistry
from mcp_serializer.initializer import MCPInitializer
from mcp_serializer.serializers import MCPSerializer
from mcp_serializer.features.prompt.result import PromptsResult

# Initialize registry at module level
registry = MCPRegistry()

# Create temporary files for testing
# Text file
temp_text_file = tempfile.NamedTemporaryFile(
    mode="w", suffix=".txt", delete=False, dir=tempfile.gettempdir()
)
temp_text_file.write("This is a sample instruction from a text file.")
temp_text_file_path = temp_text_file.name
temp_text_file.close()

# Markdown file
temp_md_file = tempfile.NamedTemporaryFile(
    mode="w", suffix=".md", delete=False, dir=tempfile.gettempdir()
)
temp_md_file.write("# Documentation\n\nThis is markdown content for prompts.")
temp_md_file_path = temp_md_file.name
temp_md_file.close()

# JSON file for embedded resource
temp_json_file = tempfile.NamedTemporaryFile(
    mode="w", suffix=".json", delete=False, dir=tempfile.gettempdir()
)
temp_json_file.write(json.dumps({"example": "data", "type": "config"}))
temp_json_file_path = temp_json_file.name
temp_json_file.close()


@registry.prompt()
def greeting():
    """Greeting prompt

    Generate a greeting prompt."""
    content = PromptsResult()
    content.add_text(
        "Hello! How can I assist you today?", role=PromptsResult.Roles.ASSISTANT
    )
    return content


@registry.prompt()
def code_review_prompt(language: str, code_snippet: str):
    """Code review prompt

    Generate a code review prompt with context."""
    content = PromptsResult()
    content.add_text(
        f"Please review the following {language} code:", role=PromptsResult.Roles.USER
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
    content = PromptsResult()
    content.add_text(
        f"Please summarize the following document in under {max_length} words:",
        role="user",
    )
    content.add_text(document, role="user")
    return content


# Static text prompt
registry.add_text_prompt(
    name="welcome",
    text="Welcome to our service! How can we help you today?",
    role="user",
    title="Welcome Prompt",
    description="A welcoming prompt for users",
)

# Static text prompt with mime type
registry.add_text_prompt(
    name="markdown_guide",
    text="# Quick Guide\n\nHere are some tips to get started...",
    role="assistant",
    mime_type="text/markdown",
    title="Markdown Guide",
    description="A guide in markdown format",
)

# Static file-based prompts using file path (string)
registry.add_file_prompt(
    name="file_instruction",
    file=temp_text_file_path,
    role="user",
    title="File Instruction",
    description="Instruction loaded from a text file",
)

registry.add_file_prompt(
    name="markdown_file_guide",
    file=temp_md_file_path,
    role="assistant",
    title="Markdown File Guide",
    description="Guide loaded from a markdown file",
)

# Static file-based prompt using file object (BinaryIO) - opened
with open(temp_text_file_path, "rb") as file_obj:
    registry.add_file_prompt(
        name="file_object_instruction",
        file=file_obj,
        role="user",
        title="File Object Instruction",
        description="Instruction loaded from a file object",
    )


# Prompt function using add_file_message and add_file_resource with file paths
@registry.prompt()
def documentation_prompt(section: str):
    """Documentation prompt with files

    Generate documentation prompt with file content and embedded resources."""
    result = PromptsResult()

    # Add text message
    result.add_text(
        f"Here is the documentation for {section}:", role=PromptsResult.Roles.USER
    )

    # Add file content as message (using file path)
    result.add_file_message(file=temp_md_file_path, role=PromptsResult.Roles.USER)

    # Add file as embedded resource (using file path)
    result.add_file_resource(file=temp_json_file_path, role=PromptsResult.Roles.USER)

    return result


# Prompt function using add_file_message and add_file_resource with file objects
@registry.prompt()
def file_object_prompt(topic: str):
    """File object prompt

    Generate prompt using file objects instead of paths."""
    result = PromptsResult()

    # Add text message
    result.add_text(f"Topic: {topic}", role=PromptsResult.Roles.USER)

    # Add file content as message (using file object)
    with open(temp_text_file_path, "rb") as f:
        result.add_file_message(file=f, role=PromptsResult.Roles.USER)

    # Add file as embedded resource (using file object)
    with open(temp_json_file_path, "rb") as f:
        result.add_file_resource(file=f, role=PromptsResult.Roles.ASSISTANT)

    return result


# ============================================================================
# Create Initializer and Serializer
# ============================================================================

initializer = MCPInitializer(
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
    assert response.response_data["jsonrpc"] == "2.0"
    assert response.response_data["id"] == 1
    assert "result" in response.response_data
    assert response.response_data["result"]["protocolVersion"] == "2024-11-05"
    assert "serverInfo" in response.response_data["result"]
    assert (
        response.response_data["result"]["serverInfo"]["name"]
        == "test-mcp-server-prompts"
    )
    assert "capabilities" in response.response_data["result"]
    assert "prompts" in response.response_data["result"]["capabilities"]


def test_prompts_list_request():
    """Test listing available prompts."""
    request = {"jsonrpc": "2.0", "id": 8, "method": "prompts/list", "params": {}}

    response = serializer.process_request(request)

    assert response is not None
    assert response.response_data["jsonrpc"] == "2.0"
    assert response.response_data["id"] == 8
    assert "result" in response.response_data
    assert "prompts" in response.response_data["result"]
    assert len(response.response_data["result"]["prompts"]) == 10
    # greeting, code_review, summarize, welcome, markdown_guide,
    # file_instruction, markdown_file_guide, file_object_instruction,
    # documentation_prompt, file_object_prompt

    prompt_names = [
        prompt["name"] for prompt in response.response_data["result"]["prompts"]
    ]
    assert "greeting" in prompt_names
    assert "code_review_prompt" in prompt_names
    assert "summarize" in prompt_names
    assert "welcome" in prompt_names
    assert "markdown_guide" in prompt_names
    assert "file_instruction" in prompt_names
    assert "markdown_file_guide" in prompt_names
    assert "file_object_instruction" in prompt_names
    assert "documentation_prompt" in prompt_names
    assert "file_object_prompt" in prompt_names


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
    assert response.response_data["jsonrpc"] == "2.0"
    assert response.response_data["id"] == 9
    assert "result" in response.response_data
    assert "messages" in response.response_data["result"]
    assert "Hello" in str(response.response_data["result"]["messages"])

    # Test code review prompt with parameters
    request = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "prompts/get",
        "params": {
            "name": "code_review_prompt",
            "arguments": {
                "language": "Python",
                "code_snippet": "def hello():\n    print('world')",
            },
        },
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response.response_data
    assert "messages" in response.response_data["result"]
    assert "Python" in str(response.response_data["result"]["messages"])


def test_static_text_prompts():
    """Test getting static text prompts."""
    # Test welcome prompt
    request = {
        "jsonrpc": "2.0",
        "id": 13,
        "method": "prompts/get",
        "params": {"name": "welcome"},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response.response_data
    assert "messages" in response.response_data["result"]
    assert len(response.response_data["result"]["messages"]) == 1
    assert response.response_data["result"]["messages"][0]["role"] == "user"
    assert (
        "Welcome to our service"
        in response.response_data["result"]["messages"][0]["content"]["text"]
    )
    assert (
        response.response_data["result"]["description"]
        == "A welcoming prompt for users"
    )

    # Test markdown guide prompt
    request = {
        "jsonrpc": "2.0",
        "id": 14,
        "method": "prompts/get",
        "params": {"name": "markdown_guide"},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response.response_data
    assert response.response_data["result"]["messages"][0]["role"] == "assistant"
    assert (
        "# Quick Guide"
        in response.response_data["result"]["messages"][0]["content"]["text"]
    )
    assert (
        response.response_data["result"]["messages"][0]["content"]["mimeType"]
        == "text/markdown"
    )


def test_file_based_prompts():
    """Test static file-based prompts using file paths."""
    # Test text file prompt (file path)
    request = {
        "jsonrpc": "2.0",
        "id": 15,
        "method": "prompts/get",
        "params": {"name": "file_instruction"},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response.response_data
    assert "messages" in response.response_data["result"]
    assert len(response.response_data["result"]["messages"]) == 1
    assert response.response_data["result"]["messages"][0]["role"] == "user"
    assert (
        "sample instruction from a text file"
        in response.response_data["result"]["messages"][0]["content"]["text"]
    )
    assert (
        response.response_data["result"]["messages"][0]["content"]["mimeType"]
        == "text/plain"
    )

    # Test markdown file prompt (file path)
    request = {
        "jsonrpc": "2.0",
        "id": 16,
        "method": "prompts/get",
        "params": {"name": "markdown_file_guide"},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response.response_data
    assert response.response_data["result"]["messages"][0]["role"] == "assistant"
    assert (
        "# Documentation"
        in response.response_data["result"]["messages"][0]["content"]["text"]
    )
    assert (
        response.response_data["result"]["messages"][0]["content"]["mimeType"]
        == "text/markdown"
    )

    # Test file object prompt (BinaryIO)
    request = {
        "jsonrpc": "2.0",
        "id": 18,
        "method": "prompts/get",
        "params": {"name": "file_object_instruction"},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response.response_data
    assert "messages" in response.response_data["result"]
    assert len(response.response_data["result"]["messages"]) == 1
    assert response.response_data["result"]["messages"][0]["role"] == "user"
    assert (
        "sample instruction from a text file"
        in response.response_data["result"]["messages"][0]["content"]["text"]
    )
    assert (
        response.response_data["result"]["messages"][0]["content"]["mimeType"]
        == "text/plain"
    )


def test_prompt_with_file_methods():
    """Test prompt function using add_file_message and add_file_resource with file paths."""
    request = {
        "jsonrpc": "2.0",
        "id": 17,
        "method": "prompts/get",
        "params": {"name": "documentation_prompt", "arguments": {"section": "API"}},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response.response_data
    assert "messages" in response.response_data["result"]
    assert len(response.response_data["result"]["messages"]) == 3

    # First message - text
    assert response.response_data["result"]["messages"][0]["role"] == "user"
    assert (
        "documentation for API"
        in response.response_data["result"]["messages"][0]["content"]["text"]
    )

    # Second message - file content via add_file_message (file path)
    assert response.response_data["result"]["messages"][1]["role"] == "user"
    assert response.response_data["result"]["messages"][1]["content"]["type"] == "text"
    assert (
        "# Documentation"
        in response.response_data["result"]["messages"][1]["content"]["text"]
    )
    assert (
        response.response_data["result"]["messages"][1]["content"]["mimeType"]
        == "text/markdown"
    )

    # Third message - embedded resource via add_file_resource (file path)
    assert response.response_data["result"]["messages"][2]["role"] == "user"
    assert (
        response.response_data["result"]["messages"][2]["content"]["type"] == "resource"
    )
    resource = response.response_data["result"]["messages"][2]["content"]["resource"]
    assert "text" in resource
    assert '"example": "data"' in resource["text"]
    assert resource["mimeType"] == "application/json"


def test_prompt_with_file_objects():
    """Test prompt function using add_file_message and add_file_resource with file objects."""
    request = {
        "jsonrpc": "2.0",
        "id": 19,
        "method": "prompts/get",
        "params": {"name": "file_object_prompt", "arguments": {"topic": "Testing"}},
    }

    response = serializer.process_request(request)

    assert response is not None
    assert "result" in response.response_data
    assert "messages" in response.response_data["result"]
    assert len(response.response_data["result"]["messages"]) == 3

    # First message - text
    assert response.response_data["result"]["messages"][0]["role"] == "user"
    assert (
        "Topic: Testing"
        in response.response_data["result"]["messages"][0]["content"]["text"]
    )

    # Second message - file content via add_file_message (file object)
    assert response.response_data["result"]["messages"][1]["role"] == "user"
    assert response.response_data["result"]["messages"][1]["content"]["type"] == "text"
    assert (
        "sample instruction from a text file"
        in response.response_data["result"]["messages"][1]["content"]["text"]
    )
    assert (
        response.response_data["result"]["messages"][1]["content"]["mimeType"]
        == "text/plain"
    )

    # Third message - embedded resource via add_file_resource (file object)
    assert response.response_data["result"]["messages"][2]["role"] == "assistant"
    assert (
        response.response_data["result"]["messages"][2]["content"]["type"] == "resource"
    )
    resource = response.response_data["result"]["messages"][2]["content"]["resource"]
    assert "text" in resource
    assert '"example": "data"' in resource["text"]
    assert resource["mimeType"] == "application/json"


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

    response_context = serializer.process_request(batch_request)

    assert response_context is not None
    assert isinstance(response_context.response_data, list)
    assert len(response_context.response_data) == 2
    assert len(response_context.history) == 2
    assert all("result" in resp for resp in response_context.response_data)


def test_cleanup():
    """Clean up temporary files."""
    if os.path.exists(temp_text_file_path):
        os.unlink(temp_text_file_path)
    if os.path.exists(temp_md_file_path):
        os.unlink(temp_md_file_path)
    if os.path.exists(temp_json_file_path):
        os.unlink(temp_json_file_path)
