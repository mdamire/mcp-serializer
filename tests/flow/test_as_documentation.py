import tempfile
import json

from mcp_serializer.registry import MCPRegistry
from mcp_serializer.initializer import Initializer
from mcp_serializer.serializers import MCPSerializer

# define names to test
request_data = {}

temp_file = tempfile.NamedTemporaryFile(
    mode="w", suffix=".json", delete=False, dir=tempfile.gettempdir()
)
temp_file.write(json.dumps({"test": "data", "version": "1.0"}))
temp_file_path = temp_file.name
temp_file.close()


##Package description: Easily define your MCP features. It takes a MCP request and returns a mcp response data with your 
#defined features.

#### Feature registrations
registry = MCPRegistry()

### Registering resources:
## you can register a file as resource
registry.add_file_resource(
    file=temp_file_path, title="File Resource Title"
)
# The file can be a file path or a file object. You can supply custom uri as `uri` parameter. 


## you can register a http resource
registry.add_http_resource(
    uri="https://example.com/image.png",
    title="This is a test image",
)

## for complex cases you can return a ResourceResult object from a function. Functions with parameters creates a resource template.
from mcp_serializer.features.resource.result import ResourceResult
@registry.resource(uri="resource/weather/")
def get_weather(city: str):
    """Get weather information for a given city
    
    This returns a different data for weather of a city. 
    The "temp.json" file contains the weather data for the city.
    the "wind.json" file contains the wind data for the city.
    the "heatmap.png" file contains the heatmap of the city.
    """


    result = ResourceResult()
    result.add_file("temp.json")
    result.add_file("wind.json")
    result.add_file("heatmap.png")

    return result

# This will create a resource template with the uri "resource/weather/{city}", name will be function name, titile will be 
# function title which is line of the function documentation followed by a new line and the description will be the function documentation.

### Registering tools:
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
    result.add_file("weather.json")

    # already defined resources can be used as resource links
    result.add_resource_link(uri="resource/weather/{city}", registry=registry) # this will be a resource link
    return result


### Registering a prompt
## register a text prompt
registry.add_text_prompt(
    name="greeting",
    text="Hello, how are you?",
    role="user",
)

# The name and text is mandatory. role is optional but highly recommended. Role can be "user" or "assistant".

## registering a text prompt from file
registry.add_file_prompt(
    name="greeting",
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
    result = PromptsResult()
    # this will create a text prompt content which is same as only returning a string from the function.
    result.add_text(f"Hello, {name}! How are you?", role="user")
    
    # This will also create a text prompt but from a file.
    result.add_file_message("file.md")

    # you can embade a resource with you prompt
    result.add_file_resource("file.txt")
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
mcp_response_data = serializer.process_request(request_data={})

# the page_size is the number of items to return in a single page for listing features.
# request_data is the request data for the MCP request. It can be a JSON string, a JSON object or a list of JSON objects.

