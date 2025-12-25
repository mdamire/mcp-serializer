# MCP Serializer

**Register MCP features and serialize JSON-RPC requests into response data.**

MCP Serializer is a Python library that handles the Model Context Protocol (MCP) serialization layer for your server. It provides:

- **Feature Registration**: Define tools, prompts, and resources using simple decorators and functions
- **Request Processing**: Process incoming JSON-RPC requests and get properly formatted MCP response data

This library focuses on the protocol implementation - you register what your server can do, and the serializer handles converting requests into responses. You're responsible for the transport layer (HTTP, stdio, or any other communication method) and wiring up the request/response cycle with your chosen framework.

## Installation

```bash
pip install mcp-serializer
```

## Feature Registration

A registry instance is needed to register tools, prompts, and resources.

```python
from mcp_serializer.registry import MCPRegistry

registry = MCPRegistry()
```

<br>

### 1. Registering Resources

#### Register a file as a resource. The file parameter is required and can be a file path or a file object.

```python
registry.add_file_resource(
    file="/path/to/file.json",
    title="File Resource Title",
    description="This is a file resource",
)
```

The file will be automatically converted to text or binary content based on the mime type parsed from the file extension. You can supply a custom URI using the `uri` parameter, otherwise it will be generated from the file path.

#### Register an HTTP resource by providing a URI. The URI is the only required parameter.

```python
registry.add_http_resource(
    uri="https://example.com/image.png",
    title="Profile Image",
    description="This image can be used as a profile image for a user.",
    mime_type="image/png",
    size=1024,
)
```

The mime type will be taken from the `mime_type` parameter or will be automatically determined from the URI extension.

#### For complex cases, register a resource using a function that returns a `ResourceResult` object. Functions with parameters create resource templates with URI placeholders.

```python
from mcp_serializer.results import ResourceResult

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

    # Add file as resource (converted to text/binary based on file extension)
    result.add_file("/path/to/weather_file.json")

    return result
```

This creates a resource template with URI `resource/weather/{city}`. The function name becomes the resource name. The first line of the docstring becomes the title, and the rest becomes the description.

<br>

### 2. Registering Tools


#### A function can be registered as a tool by using the `@registry.tool()` decorator.

```python
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
```

The function name becomes the tool name. The docstring is parsed as Google-style docstring:
- First line(s) followed by a new line becomes the title
- Description is the text until the Args section
- Parameter description from Args section is used as description for the tool's input schema


#### For structured data, return a Pydantic `BaseModel`. The model must be specified as the return type.

```python
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
```

The Pydantic model will be automatically converted to an output schema in the tool definition.

#### For complex responses with multiple content types, return a `ToolsResult` object.

```python
from mcp_serializer.results import ToolsResult

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
        f"{days}-day forecast for {city}: Mostly sunny with temperatures around 70�F"
    )

    # Add embedded file resource
    result.add_file("/path/to/file.json")

    # Add resource link to an existing resource
    result.add_resource_link(uri="resource/weather/{city}", registry=registry)

    return result
```

`ToolsResult` also has `add_image_content` and `add_audio_content` functions to add contents manually.

<br>

### 3. Registering Prompts

#### Register a text prompt directly.

```python
registry.add_text_prompt(
    name="greeting",
    text="Hello, how are you?",
    title="Greeting a user and asking common questions",
    role="user",
)
```

The name and text are mandatory. Role can be "user" or "assistant" and defaults to "user".

#### Register a text prompt from a file.

```python
registry.add_file_prompt(
    name="create_user",
    description="Create a new user for any purpose.",
    file="/path/to/prompt.txt",
    role="user",
)
```

The file can be a file path or a file object. You can supply title and description as parameters for these registration methods. These are useful for the client to understand the prompt.

#### A function can be registered to create a prompt. It can return a string, a tuple (text, role), or a `PromptsResult` object.

```python
from mcp_serializer.results import PromptsResult

@registry.prompt()
def greeting_prompt(name: str):
    """Greeting prompt

    This prompt helps to greet a user.
    """
    result = PromptsResult()

    # Create a text prompt content (same as returning a string)
    result.add_text(f"Hello, {name}! How are you?", role=PromptsResult.Roles.USER)

    # Create a text prompt from a file
    result.add_file_message("/path/to/message.md")

    # Embed a resource with your prompt
    result.add_file_resource("/path/to/resource.json")

    return result
```

This creates a prompt with the name "greeting_prompt". The function docstring is parsed as Google-style:
- Title will be the first lines of docstring followed by a new line
- The description will be the rest of the docstring

<br>

## Initializer

An initializer is needed to return the MCP initialization data. You need to add your features to present at initialization time.

```python
from mcp_serializer.initializer import MCPInitializer

initializer = MCPInitializer()
initializer.add_server_info("My MCP Server", "1.0.0", "A title of the server.")
initializer.add_prompt()
initializer.add_resources()
initializer.add_tools()
```

### Custom Initializer

You can create your own initializer by inheriting from the `MCPInitializer` class. You can override the `build_result` method to initialize MCP client parameters.

```python
class MyInitializer(MCPInitializer):
    def build_result(self, client_params: dict):
        self.protocol_version = client_params.get(
            "protocolVersion", self.protocol_version
        )
        return super().build_result(client_params)
```

<br>

## Creating and Using the Serializer

```python
from mcp_serializer.serializers import MCPSerializer

serializer = MCPSerializer(initializer=initializer, registry=registry, page_size=10)
```

The `page_size` is the number of items to return in a single page for listing features.

### Processing Requests

The `process_request` method takes a JSON-RPC request and returns a `ResponseContext` object. The `ResponseContext` provides access to the response data and maintains a history of all request-response interactions.

```python
response_context = serializer.process_request(
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

# Access the response data as a dictionary (ready to send to client)
response_dict = response_context.response_data

# Access detailed information through history
for entry in response_context.history:
    # Each entry contains:
    # - entry.response: Pydantic response object (JsonRpcSuccessResponse/JsonRpcErrorResponse)
    # - entry.request: Pydantic request object (JsonRpcRequest)
    # - entry.data: Response as dictionary
    # - entry.is_error: Boolean indicating if this is an error
    # - entry.is_notification: Boolean indicating if this is a notification
    
    if entry.is_error:
        print("Error:", entry.data["error"])
    elif entry.is_notification:
        print("Notification - no response to send")
    else:
        print("Success:", entry.data["result"])
```

The `request_data` parameter can be a dict or a JSON string.

**ResponseContext Properties:**
- `response_data`: The response as a dictionary or list of dictionaries (for batch requests), ready to be serialized to JSON and sent to the client
- `history`: List of `ResponseEntry` objects, one per request processed

**ResponseEntry Properties (accessible via `response_context.history[i]`):**
- `response`: The Pydantic BaseModel response object (`JsonRpcSuccessResponse`, `JsonRpcErrorResponse`, or `None` for notifications)
  - `JsonRpcSuccessResponse` properties: `jsonrpc`, `id`, `result`
  - `JsonRpcErrorResponse` properties: `jsonrpc`, `id`, `error`
- `request`: The Pydantic BaseModel request object (`JsonRpcRequest`)
  - `JsonRpcRequest` properties: `jsonrpc`, `id`, `method`, `params`
- `data`: The response as a dictionary (same as the corresponding item in `response_data`)
- `is_error`: Boolean property indicating if this is an error response
- `is_notification`: Boolean property indicating if this was a notification (no response needed)

<br>

## Examples

The following examples demonstrate the complete request-response cycle using the features registered in this documentation. If you follow the registration steps outlined above and create a serializer with the same configuration, you can expect these exact request-response patterns.

### Initialization

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "My MCP Server",
            "title": "A title of the server.",
            "version": "1.0.0"
        },
        "capabilities": {
            "prompts": {"listChanged": false},
            "resources": {"subscribe": false, "listChanged": false},
            "tools": {"listChanged": false}
        }
    }
}
```

### Tools

#### List Tools

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
}
```

**Response:**
```json
{
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
                            "description": "The name of the city"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "The temperature in Fahrenheit"
                        },
                        "wind_speed": {
                            "type": "number",
                            "description": "The wind speed in mph"
                        },
                        "humidity": {
                            "type": "number",
                            "description": "The humidity percentage"
                        }
                    },
                    "required": ["city", "temperature"]
                }
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
                            "description": "The name of the city"
                        }
                    },
                    "required": ["city"]
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "temperature": {"type": "number"},
                        "condition": {"type": "string"},
                        "humidity": {"type": "number"}
                    },
                    "required": ["temperature", "condition", "humidity"]
                }
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
                            "description": "The name of the city"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to forecast (default: 3)"
                        }
                    },
                    "required": ["city"]
                }
            }
        ]
    }
}
```

#### Call Tool - Simple String Return

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "add_weather_data",
        "arguments": {
            "city": "London",
            "temperature": 15.5,
            "wind_speed": 10.0,
            "humidity": 80.0
        }
    }
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 3,
    "result": {
        "content": [
            {"type": "text", "text": "Weather data for London added successfully"}
        ]
    }
}
```

#### Call Tool - Pydantic Model Return

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "get_current_weather",
        "arguments": {
            "city": "Paris"
        }
    }
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 3,
    "result": {
        "content": [],
        "structuredContent": {
            "condition": "sunny",
            "humidity": 65.0,
            "temperature": 72.5
        }
    }
}
```

#### Call Tool - ToolsResult with Multiple Content Types

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "get_weather_forecast",
        "arguments": {"city": "Tokyo", "days": 5}
    }
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 3,
    "result": {
        "content": [
            {
                "type": "text",
                "text": "5-day forecast for Tokyo: Mostly sunny with temperatures around 70�F"
            },
            {
                "type": "resource",
                "resource": {
                    "uri": "file:///path/to/file.json",
                    "mimeType": "application/json",
                    "name": "file.json",
                    "text": "{\"test\": \"data\", \"version\": \"1.0\"}"
                }
            },
            {
                "type": "resource_link",
                "uri": "resource/weather/{city}",
                "name": "get_weather",
                "title": "Get weather information for a given city",
                "description": "Returns weather data for the specified city including temperature and conditions."
            }
        ]
    }
}
```

### Prompts

#### List Prompts

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "prompts/list",
    "params": {}
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 4,
    "result": {
        "prompts": [
            {
                "name": "create_user",
                "description": "Create a new user for any purpose."
            },
            {
                "name": "greeting",
                "title": "Greeting a user and asking common questions"
            },
            {
                "name": "greeting_prompt",
                "title": "Greeting prompt",
                "description": "This prompt helps to greet a user.",
                "arguments": [{"name": "name", "type": "string", "required": true}]
            }
        ]
    }
}
```

#### Get Simple Prompt

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "prompts/get",
    "params": {"name": "greeting"}
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 5,
    "result": {
        "messages": [
            {
                "role": "user",
                "content": {"type": "text", "text": "Hello, how are you?"}
            }
        ]
    }
}
```

#### Get Prompt with Arguments

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 6,
    "method": "prompts/get",
    "params": {"name": "greeting_prompt", "arguments": {"name": "Alice"}}
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 6,
    "result": {
        "description": "This prompt helps to greet a user.",
        "messages": [
            {
                "role": "user",
                "content": {"type": "text", "text": "Hello, Alice! How are you?"}
            },
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "You are a helpful assistant that can help with any questions.",
                    "mimeType": "text/markdown"
                }
            },
            {
                "role": "user",
                "content": {
                    "type": "resource",
                    "resource": {
                        "uri": "file:///path/to/file.json",
                        "text": "File Resource Title",
                        "mimeType": "application/json",
                        "name": "file.json",
                        "text": "{\"test\": \"data\", \"version\": \"1.0\"}"
                    }
                }
            }
        ]
    }
}
```

### Resources

#### List Resources

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 7,
    "method": "resources/list",
    "params": {}
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 7,
    "result": {
        "resources": [
            {
                "uri": "file:///path/to/file.json",
                "name": "file.json",
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
```

#### List Resource Templates

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 8,
    "method": "resources/templates/list",
    "params": {}
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 8,
    "result": {
        "resourceTemplates": [
            {
                "uri": "resource/weather/{city}",
                "name": "get_weather",
                "title": "Get weather information for a given city",
                "description": "Returns weather data for the specified city including temperature and conditions."
            }
        ]
    }
}
```

#### Read File Resource

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 10,
    "method": "resources/read",
    "params": {"uri": "file:///path/to/file.json"}
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 10,
    "result": {
        "contents": [
            {
                "uri": "file:///path/to/file.json",
                "name": "file.json",
                "title": "File Resource Title",
                "mimeType": "application/json",
                "text": "{\"test\": \"data\", \"version\": \"1.0\"}"
            }
        ]
    }
}
```

#### Read Resource Template with Parameters

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 12,
    "method": "resources/read",
    "params": {"uri": "resource/weather/Paris"}
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 12,
    "result": {
        "contents": [
            {
                "mimeType": "text/plain",
                "name": "get_weather",
                "title": "indicated cold/hot in the city",
                "text": "today is cold in Paris",
                "uri": "resource/weather"
            },
            {
                "uri": "file:///path/to/weather_file.json",
                "mimeType": "application/json",
                "name": "weather_file.json",
                "text": "{\"temperature\": 72, \"condition\": \"sunny\"}"
            }
        ]
    }
}
```

### Error Handling

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 12,
    "method": "invalid/method",
    "params": {}
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": 12,
    "error": {
        "code": -32601,
        "message": "Method not found",
        "data": {"method": "invalid/method"}
    }
}
```

### Batch Requests

**Request:**
```json
[
    {"jsonrpc": "2.0", "id": 13, "method": "tools/list", "params": {}},
    {"jsonrpc": "2.0", "id": 14, "method": "prompts/list", "params": {}},
    {"jsonrpc": "2.0", "id": 15, "method": "resources/list", "params": {}}
]
```

**Response:**
```json
[
    {"jsonrpc": "2.0", "id": 13, "result": {...}},
    {"jsonrpc": "2.0", "id": 14, "result": {...}},
    {"jsonrpc": "2.0", "id": 15, "result": {...}}
]
```

## License

MIT
