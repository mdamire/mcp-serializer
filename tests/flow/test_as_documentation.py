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
# Easily define your MCP features. It takes a MCP request and returns a mcp response data with your defined features.


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
    result.add_text_content(f"today is cold in {city}", mime_type="text/plain", title="indicated cold/hot in the city")

    # Add file as resource (same as add_file_resource, converted to text/binary based on file extension)
    result.add_file(temp_weather_file_path)

    return result

# This creates a resource template with URI "resource/weather/{city}".
# The function name becomes the resource name. The first line of the docstring becomes the title. Rest of the docstring 
# becomes the description.



### 3. Registering tools:
## you can register a function as a tool
@registry.tool()
def add_weather_data(city: str, temperature: float, wind_speed: float, humidity: float):
    """Add weather data for a given city
    
    This adds weather data for a given city.

    Args:
        city: The city to add weather data for
        temperature: The temperature of the city
        wind_speed: The wind speed of the city
        humidity: The humidity of the city
    """
    # Other logic to add weather data
    return f"Weather data for {city} added successfully"

# This will create a tool with the name "add_weather_data". The function documentation will be parsed as google docstring style. Title will be function title which is line of the function documentation followed by a new line and the description will be the function documentation until arguments section.
# The tool's arguments definition will be created from function parameters name, type and default value. The argument description comes from the function documentation after the arguments section.

## you can return a structured result from a tool function. You need return a Pydantic BaseModel instance. It must be also as return type of the function.
from pydantic import BaseModel
class WeatherData(BaseModel):
    temperature: float
    wind_speed: float
    humidity: float

@registry.tool()
def get_weather_data(city: str) -> WeatherData:
    """Get weather data for a given city
    
    This returns weather data for a given city.
    """
    return WeatherData(temperature=20, wind_speed=10, humidity=50)


## for more complex cases of non structured results you can return a ToolsResult object
from mcp_serializer.features.tool.result import ToolsResult
@registry.tool()
def get_weather_data(city: str) -> ToolsResult:
    """Get weather data for a given city
    
    This returns weather data for a given city.
    """
    result = ToolsResult()
    # this will create a text content which is same as only returning a string from the function.
    result.add_text_content(f"Weather data for {city} is 20 degrees")

    # files can be added as embedded resources
    result.add_file(temp_file_path)

    # already defined resources can be used as resource links
    result.add_resource_link(uri="resource/weather/{city}", registry=registry) # this will be a resource link
    return result


### Registering a prompt
## register a text prompt
registry.add_text_prompt(
    name="greeting",
    text="Hello, how are you?",
    title="Geeting a user and asking common questions",
    role="user",
)

# The name and text is mandatory. role is optional but highly recommended. Role can be "user" or "assistant".

## registering a text prompt from file
registry.add_file_prompt(
    name="create_user",
    description="Create a new use for any purpose.",
    file=temp_file_path,
    role="user",
)
# the file can be a file path or a file object. 
# You can supply title and description as parameters for these prompts. These are useful for the client to understand the prompt.

## for complex cases you can return a PromptsResult object from a function.
from mcp_serializer.features.prompt.result import PromptsResult
@registry.prompt()
def greeting_prompt(name: str):
    """Greeting prompt
    
    This returns a greeting prompt.
    """
    result = PromptsResult(description="A description of how the result will be used.")
    # this will create a text prompt content which is same as only returning a string from the function.
    result.add_text(f"Hello, {name}! How are you?", role="user")
    
    # This will also create a text prompt but from a file.
    result.add_file_message(temp_file_message_path)

    # you can embade a resource with you prompt
    result.add_file_resource(temp_file_path)
    return result
# This will create a prompt with the name "greeting_prompt". The function documentation will be parsed as google docstring style. 
# Title will be function title which is line of the function documentation followed by a new line and the description will be the function documentation.


### Creating a initializer
## initializer will help return the MCP initialization data.
initializer = Initializer()
initializer.add_server_info("My MCP Server", "1.0.0")
initializer.add_prompt()
initializer.add_resources()
initializer.add_tools()

# you can create your own initializer by inheriting from Initializer class. You can override build_result method to 
# initialize MCP client parameters.

class MyInitializer(Initializer):
    def build_result(self, client_params: dict):
        self.protocol_version = client_params.get("protocolVersion", self.protocol_version)
        return super().build_result(client_params)


### Creating a serializer
from mcp_serializer.serializers import MCPSerializer
serializer = MCPSerializer(initializer=initializer, registry=registry, page_size=10)

# the page_size is the number of items to return in a single page for listing features.
# request_data is the request data for the MCP request. It can be a JSON string, a JSON object or a list of JSON objects.


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
            "serverInfo": {"name": "My MCP Server", "version": "1.0.0"},
            "capabilities": {
                "prompts": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "tools": {"listChanged": False}
            }
        }
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
                    "description": "This adds weather data for a given city.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "The city to add weather data for"},
                            "temperature": {"type": "number", "description": "The temperature of the city"},
                            "wind_speed": {"type": "number", "description": "The wind speed of the city"},
                            "humidity": {"type": "number", "description": "The humidity of the city"}
                        },
                        "required": ["city", "temperature", "wind_speed", "humidity"]
                    }
                },
                {
                    "name": "get_weather_data",
                    "title": "Get weather data for a given city",
                    "description": "This returns weather data for a given city.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"}
                        },
                        "required": ["city"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "temperature": {"type": "number"},
                            "wind_speed": {"type": "number"},
                            "humidity": {"type": "number"}
                        },
                        "required": ["temperature", "wind_speed", "humidity"]
                    }
                },
                {
                    "name": "get_weather_data",
                    "title": "Get weather data for a given city",
                    "description": "This returns weather data for a given city.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"}
                        },
                        "required": ["city"]
                    }
                }
            ],
            "nextCursor": None
        }
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
                {
                    "type": "text",
                    "text": "Weather data for London added successfully"
                }
            ]
        }
    }

    assert response == expected_response

    # Test 2: get_weather_data (first registration) - Pydantic BaseModel return
    request = {
        "jsonrpc": "2.0",
        "id": 3.1,
        "method": "tools/call",
        "params": {
            "name": "get_weather_data",
            "arguments": {
                "city": "Paris",
            },
        },
    }

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 3.1,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": '{"temperature": 20.0, "wind_speed": 10.0, "humidity": 50.0}'
                }
            ]
        }
    }

    assert response == expected_response

    # Test 3: get_weather_data (second registration) - ToolsResult with text and file
    request = {
        "jsonrpc": "2.0",
        "id": 3.2,
        "method": "tools/call",
        "params": {
            "name": "get_weather_data",
            "arguments": {
                "city": "Tokyo",
            },
        },
    }

    response = serializer.process_request(request)

    expected_response = {
        "jsonrpc": "2.0",
        "id": 3.2,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": "Weather data for Tokyo is 20 degrees"
                },
                {
                    "type": "resource",
                    "resource": {
                        "uri": f"file://{temp_file_path}",
                        "mimeType": "application/json",
                        "name": temp_file_path.split('/')[-1],
                        "text": '{"test": "data", "version": "1.0"}'
                    }
                },
                {
                    "type": "resource",
                    "resource": {
                        "uri": "resource/weather/{city}",
                        "mimeType": "application/json"
                    }
                }
            ]
        }
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
                    "description": "This returns a greeting prompt.",
                    "arguments": [
                        {
                            "name": "name",
                            "type": "string",
                            "required": True
                        }
                    ]
                }
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
                    "content": {
                        "type": "text",
                        "text": "Hello, how are you?"
                    }
                }
            ]
        }
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
            "description": "A description of how the result will be used.",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": "Hello, Alice! How are you?"
                    }
                },
                {
                    "role": "user",
                    "content": {
                        'type': 'text', 
                        'text': 'You are a helpful assistant that can help with any questions.', 
                        'mimeType': 'text/markdown'
                    }
                },
                {
                    "role": "user",
                    "content": {
                        'type': 'resource', 
                        'resource': {
                            'uri': f'file://{temp_file_path}',
                            'text': 'File Resource Title',
                            'mimeType': 'application/json',
                            'name': temp_file_path.split('/')[-1],
                            'text': '{"test": "data", "version": "1.0"}'
                        }
                    }
                }
            ]
        }
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
                    "name": temp_file_path.split('/')[-1],
                    "title": "File Resource Title",
                    "description": "This is a file resource",
                    "size": 34,
                    "mimeType": "application/json"
                },
                {
                    "uri": "https://example.com/image.png",
                    "title": "Profile Image",
                    "description": "This image can be used as a profile image for a user.",
                    "size": 1024,
                    "mimeType": "image/png"
                }
            ]
        }
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
        }
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
                    "name": temp_file_path.split('/')[-1],
                    "title": "File Resource Title",
                    "mimeType": "application/json",
                    "text": '{"test": "data", "version": "1.0"}'
                }
            ]
        }
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

    # For multiple content in same resource, it doesn't inherit information from the definition.
    expected_response = {
        "jsonrpc": "2.0",
        "id": 12,
        "result": {
            "contents": [
                {
                    'mimeType': 'text/plain',
                    'title': 'indicated cold/hot in the city',
                    'text': 'today is cold in Paris',
                },
                {
                    'uri': f"file://{temp_weather_file_path}",
                    'mimeType': 'application/json',
                    'name': temp_weather_file_path.split('/')[-1],
                    'text': '{"temperature": 72, "condition": "sunny"}',
                },
            ]
        }
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
            "data": {
                "method": "invalid/method"
            }
        }
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

    expected_responses = [
        {
            "jsonrpc": "2.0",
            "id": 13,
            "result": {
                "tools": [
                    {
                        "name": "add_weather_data",
                        "title": "Add weather data for a given city",
                        "description": "This adds weather data for a given city.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string", "description": "The city to add weather data for"},
                                "temperature": {"type": "number", "description": "The temperature of the city"},
                                "wind_speed": {"type": "number", "description": "The wind speed of the city"},
                                "humidity": {"type": "number", "description": "The humidity of the city"}
                            },
                            "required": ["city", "temperature", "wind_speed", "humidity"]
                        }
                    },
                    {
                        "name": "get_weather_data",
                        "title": "Get weather data for a given city",
                        "description": "This returns weather data for a given city.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string"}
                            },
                            "required": ["city"]
                        },
                        "outputSchema": {
                            "type": "object",
                            "properties": {
                                "temperature": {"type": "number"},
                                "wind_speed": {"type": "number"},
                                "humidity": {"type": "number"}
                            },
                            "required": ["temperature", "wind_speed", "humidity"]
                        }
                    },
                    {
                        "name": "get_weather_data",
                        "title": "Get weather data for a given city",
                        "description": "This returns weather data for a given city.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string"}
                            },
                            "required": ["city"]
                        }
                    }
                ],
                "nextCursor": None
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 14,
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
                        "description": "This returns a greeting prompt.",
                        "arguments": [
                            {
                                "name": "name",
                                "type": "string",
                                "required": True
                            }
                        ]
                    }
                ],
                "nextCursor": None
            }
        },
        {
            "jsonrpc": "2.0",
            "id": 15,
            "result": {
                "resources": [
                    {
                        "uri": f"file://{temp_file_path}",
                        "name": temp_file_path.split('/')[-1],
                        "title": "File Resource Title",
                        "description": "This is a file resource",
                        "size": 34,
                        "mimeType": "application/json"
                    },
                    {
                        "uri": "https://example.com/image.png",
                        "title": "Profile Image",
                        "description": "This image can be used as a profile image for a user.",
                        "size": 1024,
                        "mimeType": "image/png"
                    }
                ]
            }
        }
    ]

    assert responses == expected_responses
