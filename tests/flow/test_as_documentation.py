import tempfile
import json

from mcp_serializer.registry import MCPRegistry
from mcp_serializer.initializer import Initializer
from mcp_serializer.serializers import MCPSerializer

### Helpers
request_data = {}

temp_file = tempfile.NamedTemporaryFile(
    mode="w", suffix=".json", delete=False, dir=tempfile.gettempdir()
)
temp_file.write(json.dumps({"test": "data", "version": "1.0"}))
temp_file_path = temp_file.name
temp_file.close()

temp_file_message = tempfile.NamedTemporaryFile(
    mode="w", suffix=".md", delete=False, dir=tempfile.gettempdir()
)
temp_file_message.write("You are a helpful assistant that can help with any questions.")
temp_file_message_path = temp_file_message.name
temp_file_message.close()

temp_weather_file = tempfile.NamedTemporaryFile(
    mode="w", suffix=".json", delete=False, dir=tempfile.gettempdir()
)
temp_weather_file.write(json.dumps({"temperature": 72, "condition": "sunny"}))
temp_weather_file_path = temp_weather_file.name
temp_weather_file.close()


### 0. Package description:
# MCP Serializer helps you build MCP (Model Context Protocol) servers in Python.
# Register your tools, prompts, and resources, then process JSON-RPC requests to get properly formatted MCP responses.


### 1. Feature registrations
# A registry instance is needed to register tools, prompts and resources.
registry = MCPRegistry()


### 2. Registering resources:

## Simple file resource
# Register a file as a resource. The file parameter is required and can be a file path or a file object.
registry.add_file_resource(
    file=temp_file_path,
    title="File Resource Title",
    description="This is a file resource",
)
# The file will be automatically converted to text or binary content based on the mime type parsed from the file extension.
# You can supply a custom URI using the `uri` parameter, otherwise it will be generated from the file path.


## HTTP resource
# Register an HTTP resource by providing a URI. The URI is the only required parameter.
registry.add_http_resource(
    uri="https://example.com/image.png",
    title="Profile Image",
    description="This image can be used as a profile image for a user.",
    mime_type="image/png",
    size=1024,
)
# The mime type will taken from mime_type parameter or will be automatically determined from the URI extension


# For complex cases, register a resource using a function that returns a ResourceResult object.
# Functions with parameters create resource templates with URI placeholders.
from mcp_serializer.features.resource.result import ResourceResult


@registry.resource(uri="resource/weather/")
def get_weather(city: str):
    """Get weather information for a given city

    Returns weather data for the specified city including temperature and conditions.
    """
    result = ResourceResult()

    # Add text content directly
    result.add_text_content(
        f"today is cold in {city}",
        mime_type="text/plain",
        title="indicated cold/hot in the city",
    )

    # Add file as resource (same as add_file_resource, converted to text/binary based on file extension)
    result.add_file(temp_weather_file_path)

    return result


# This creates a resource template with URI "resource/weather/{city}".
# The function name becomes the resource name. The first line of the docstring becomes the title. Rest of the docstring
# becomes the description.


### 3. Registering tools:
# A function can be registered as a tool by using the @registry.tool() decorator.
@registry.tool()
def add_weather_data(
    city: str, temperature: float, wind_speed: float = None, humidity: float = None
):
    """Add weather data for a given city

    This tool saves weather data to the database for a specific city.

    Args:
        city: The name of the city
        temperature: The temperature in Fahrenheit
        wind_speed: The wind speed in mph
        humidity: The humidity percentage
    """
    # Your logic to save weather data goes here
    return f"Weather data for {city} added successfully"


# The function name becomes the tool name.
# The docstring is parsed as Google-style docstring:
#   - First line(s) followed by a new line becomes the title
#   - Description is the text until the Args section
#   - Parameter descrition from Args section is used as description for the tool's input schema


# For structured data, return a Pydantic BaseModel. The model must be specified as the return type.
from pydantic import BaseModel


class WeatherReport(BaseModel):
    temperature: float
    condition: str
    humidity: float


@registry.tool()
def get_current_weather(city: str) -> WeatherReport:
    """Get current weather for a city

    Retrieves real-time weather information including temperature, condition, and humidity.

    Args:
        city: The name of the city
    """
    return WeatherReport(temperature=72.5, condition="sunny", humidity=65.0)


# The Pydantic model will be automatically converted to an output schema in the tool definition.

# For complex responses with multiple content types, return a ToolsResult object.
from mcp_serializer.features.tool.result import ToolsResult


@registry.tool()
def get_weather_forecast(city: str, days: int = 3) -> ToolsResult:
    """Get weather forecast for a city

    Provides a detailed weather forecast with text, data files, and resource links.

    Args:
        city: The name of the city
        days: Number of days to forecast (default: 3)
    """
    result = ToolsResult()

    # Add text content
    result.add_text_content(
        f"{days}-day forecast for {city}: Mostly sunny with temperatures around 70°F"
    )

    # Add embedded file resource
    result.add_file(temp_file_path)

    # Add resource link to an existing resource
    result.add_resource_link(uri="resource/weather/{city}", registry=registry)

    return result


# ToolsResult supports multiple content types:
#   - add_text_content(): Plain text or formatted text
#   - add_file(): Embed a file as a resource
#   - add_resource_link(): Link to a registered resource
#   - add_image_content(): Add image data
#   - add_audio_content(): Add audio data


### 4. Registering prompts:
## Register a text prompt.
registry.add_text_prompt(
    name="greeting",
    text="Hello, how are you?",
    title="Geeting a user and asking common questions",
    role="user",
)
# The name and text are mandatory. Role can be "user" or "assistant" and default is "user".

## Register a text prompt from a file.
registry.add_file_prompt(
    name="create_user",
    description="Create a new use for any purpose.",
    file=temp_file_path,
    role="user",
)
# The file can be a file path or a file object.
# You can supply title and description as parameters for these registration methods. These are useful for the client to understand the prompt.

## A function can be registered to create a prompt. It can return a string, a tuple (text, role) or a PromptsResult object.
from mcp_serializer.features.prompt.result import PromptsResult


@registry.prompt()
def greeting_prompt(name: str):
    """Greeting prompt

    This prompt helps to greet a user.
    """
    result = PromptsResult()
    # this will create a text prompt content which is same as only returning a string from the function.
    result.add_text(f"Hello, {name}! How are you?", role=PromptsResult.Roles.USER)

    # This will also create a text prompt but from a file.
    result.add_file_message(temp_file_message_path)

    # you can embade a resource with you prompt
    result.add_file_resource(temp_file_path)
    return result


# This will create a prompt with the name "greeting_prompt". The function docstring will be parsed as google docstring style.
# Title will be first lines of docstring followed by a new line.
# The description will be the rest of the docstring.


### 5. Creating a initializer
# Initializer is needed to return the MCP initialization data. You need to add your features to present at initialization time.
initializer = Initializer()
initializer.add_server_info("My MCP Server", "1.0.0", "A title of the server.")
initializer.add_prompt()
initializer.add_resources()
initializer.add_tools()


# You can create your own initializer by inheriting from Initializer class. You can override build_result method to
# initialize MCP client parameters.
class MyInitializer(Initializer):
    def build_result(self, client_params: dict):
        self.protocol_version = client_params.get(
            "protocolVersion", self.protocol_version
        )
        return super().build_result(client_params)


### 6. Creating a serializer
from mcp_serializer.serializers import MCPSerializer

serializer = MCPSerializer(initializer=initializer, registry=registry, page_size=10)
# the page_size is the number of items to return in a single page for listing features.

# The process_request method takes a JSON-RPC request and returns a JSON-RPC response object.
# It also takes care of any error response or batch requests.
response = serializer.process_request(
    request_data={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }
)
# request_data parameter can be a dict or a JSON string.


# ============================================================================
# Tests
# ============================================================================


def test_initialize():
    """Test initialization request and response."""
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

    expected_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "My MCP Server",
                "title": "A title of the server.",
                "version": "1.0.0",
            },
            "capabilities": {
                "prompts": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "tools": {"listChanged": False},
            },
        },
    }

    assert response == expected_response


def test_tools_list():
    """Test tools/list request and response."""
    request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "tools": [
                {
                    "name": "add_weather_data",
                    "title": "Add weather data for a given city",
                    "description": "This tool saves weather data to the database for a specific city.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The name of the city",
                            },
                            "temperature": {
                                "type": "number",
                                "description": "The temperature in Fahrenheit",
                            },
                            "wind_speed": {
                                "type": "number",
                                "description": "The wind speed in mph",
                            },
                            "humidity": {
                                "type": "number",
                                "description": "The humidity percentage",
                            },
                        },
                        "required": ["city", "temperature"],
                    },
                },
                {
                    "name": "get_current_weather",
                    "title": "Get current weather for a city",
                    "description": "Retrieves real-time weather information including temperature, condition, and humidity.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The name of the city",
                            }
                        },
                        "required": ["city"],
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "temperature": {"type": "number"},
                            "condition": {"type": "string"},
                            "humidity": {"type": "number"},
                        },
                        "required": ["temperature", "condition", "humidity"],
                    },
                },
                {
                    "name": "get_weather_forecast",
                    "title": "Get weather forecast for a city",
                    "description": "Provides a detailed weather forecast with text, data files, and resource links.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The name of the city",
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to forecast (default: 3)",
                            },
                        },
                        "required": ["city"],
                    },
                },
            ],
            "nextCursor": None,
        },
    }

    assert response == expected_response


def test_tools_call():
    """Test tools/call request and response for all registered tools."""

    # Test 1: add_weather_data - simple string return
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "add_weather_data",
            "arguments": {
                "city": "London",
                "temperature": 15.5,
                "wind_speed": 10.0,
                "humidity": 80.0,
            },
        },
    }

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 3,
        "result": {
            "content": [
                {"type": "text", "text": "Weather data for London added successfully"}
            ]
        },
    }

    assert response == expected_response

    # Test 2: get_current_weather - Pydantic BaseModel return
    request = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "tools/call",
        "params": {
            "name": "get_current_weather",
            "arguments": {
                "city": "Paris",
            },
        },
    }

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 3,
        "result": {
            "structuredContent": {
                "condition": "sunny",
                "humidity": 65.0,
                "temperature": 72.5,
            }
        },
    }

    assert response == expected_response

    # Test 3: get_weather_forecast - ToolsResult with text, file, and resource link
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_weather_forecast",
            "arguments": {"city": "Tokyo", "days": 5},
        },
    }

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 3,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": "5-day forecast for Tokyo: Mostly sunny with temperatures around 70°F",
                },
                {
                    "type": "resource",
                    "resource": {
                        "uri": f"file://{temp_file_path}",
                        "mimeType": "application/json",
                        "name": temp_file_path.split("/")[-1],
                        "text": '{"test": "data", "version": "1.0"}',
                    },
                },
                {
                    "type": "resource_link",
                    "uri": "resource/weather/{city}",
                    "name": "get_weather",
                    "title": "Get weather information for a given city",
                    "description": "Returns weather data for the specified city including temperature and conditions.",
                },
            ]
        },
    }

    assert response == expected_response


def test_prompts_list():
    """Test prompts/list request and response."""
    request = {"jsonrpc": "2.0", "id": 4, "method": "prompts/list", "params": {}}

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 4,
        "result": {
            "prompts": [
                {
                    "name": "create_user",
                    "description": "Create a new use for any purpose.",
                },
                {
                    "name": "greeting",
                    "title": "Geeting a user and asking common questions",
                },
                {
                    "name": "greeting_prompt",
                    "title": "Greeting prompt",
                    "description": "This prompt helps to greet a user.",
                    "arguments": [{"name": "name", "type": "string", "required": True}],
                },
            ],
            "nextCursor": None,
        },
    }

    assert response == expected_response


def test_prompts_get():
    """Test prompts/get request and response."""
    request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "prompts/get",
        "params": {"name": "greeting"},
    }

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 5,
        "result": {
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": "Hello, how are you?"},
                }
            ]
        },
    }

    assert response == expected_response


def test_prompts_get_with_arguments():
    """Test prompts/get with arguments request and response."""
    request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "prompts/get",
        "params": {"name": "greeting_prompt", "arguments": {"name": "Alice"}},
    }

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 6,
        "result": {
            "description": "This prompt helps to greet a user.",
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": "Hello, Alice! How are you?"},
                },
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": "You are a helpful assistant that can help with any questions.",
                        "mimeType": "text/markdown",
                    },
                },
                {
                    "role": "user",
                    "content": {
                        "type": "resource",
                        "resource": {
                            "uri": f"file://{temp_file_path}",
                            "text": "File Resource Title",
                            "mimeType": "application/json",
                            "name": temp_file_path.split("/")[-1],
                            "text": '{"test": "data", "version": "1.0"}',
                        },
                    },
                },
            ],
        },
    }

    assert response == expected_response


def test_resources_list():
    """Test resources/list request and response."""
    request = {"jsonrpc": "2.0", "id": 7, "method": "resources/list", "params": {}}

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 7,
        "result": {
            "resources": [
                {
                    "uri": f"file://{temp_file_path}",
                    "name": temp_file_path.split("/")[-1],
                    "title": "File Resource Title",
                    "description": "This is a file resource",
                    "size": 34,
                    "mimeType": "application/json",
                },
                {
                    "uri": "https://example.com/image.png",
                    "title": "Profile Image",
                    "description": "This image can be used as a profile image for a user.",
                    "size": 1024,
                    "mimeType": "image/png",
                },
            ]
        },
    }

    assert response == expected_response


def test_resources_templates_list():
    """Test resources/templates/list request and response."""
    request = {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "resources/templates/list",
        "params": {},
    }

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 8,
        "result": {
            "resourceTemplates": [
                {
                    "uri": "resource/weather/{city}",
                    "name": "get_weather",
                    "title": "Get weather information for a given city",
                    "description": "Returns weather data for the specified city including temperature and conditions.",
                }
            ]
        },
    }

    assert response == expected_response


def test_resources_read():
    """Test resources/read request and response for different resource types."""

    # Test 1: Read file resource
    request = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "resources/read",
        "params": {"uri": f"file://{temp_file_path}"},
    }

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 10,
        "result": {
            "contents": [
                {
                    "uri": f"file://{temp_file_path}",
                    "name": temp_file_path.split("/")[-1],
                    "title": "File Resource Title",
                    "mimeType": "application/json",
                    "text": '{"test": "data", "version": "1.0"}',
                }
            ]
        },
    }

    assert response == expected_response

    # Test 2: Read resource template with parameters (returns multiple contents)
    request = {
        "jsonrpc": "2.0",
        "id": 12,
        "method": "resources/read",
        "params": {"uri": "resource/weather/Paris"},
    }

    response = serializer.process_request(request)

    # The first content will inherit information from the resource definition.
    expected_response = {
        "jsonrpc": "2.0",
        "id": 12,
        "result": {
            "contents": [
                {
                    "mimeType": "text/plain",
                    "name": "get_weather",
                    "title": "indicated cold/hot in the city",
                    "text": "today is cold in Paris",
                    "uri": "resource/weather",
                },
                {
                    "uri": f"file://{temp_weather_file_path}",
                    "mimeType": "application/json",
                    "name": temp_weather_file_path.split("/")[-1],
                    "text": '{"temperature": 72, "condition": "sunny"}',
                },
            ]
        },
    }

    assert response == expected_response


def test_error_invalid_method():
    """Test error response for invalid method."""
    request = {"jsonrpc": "2.0", "id": 12, "method": "invalid/method", "params": {}}

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 12,
        "error": {
            "code": -32601,
            "message": "Method not found",
            "data": {"method": "invalid/method"},
        },
    }

    assert response == expected_response


def test_batch_request():
    """Test batch request processing."""
    batch_request = [
        {"jsonrpc": "2.0", "id": 13, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 14, "method": "prompts/list", "params": {}},
        {"jsonrpc": "2.0", "id": 15, "method": "resources/list", "params": {}},
    ]

    responses = serializer.process_request(batch_request)
    assert len(responses) == 3

    assert responses[0]["id"] == 13
    assert responses[1]["id"] == 14
    assert responses[2]["id"] == 15
