from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any, List, Union
from ..base.schema import JsonSchema
from ..resource.schema import TextContentSchema, BinaryContentSchema
import base64


class ToolsDefinitionSchema(BaseModel):
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    inputSchema: Optional[JsonSchema] = None
    outputSchema: Optional[JsonSchema] = None
    annotations: Optional[Dict[str, Any]] = None


class ToolsListSchema(BaseModel):
    tools: List[dict]
    nextCursor: Optional[str] = None


# Content schema classes for tools
class TextContent(BaseModel):
    type: str = "text"
    text: str


class ImageContent(BaseModel):
    type: str = "image"
    data: str  # Base64-encoded image data
    mimeType: str
    annotations: Optional[Dict[str, Any]] = None

    @field_validator("data")
    @classmethod
    def validate_base64_data(cls, v):
        try:
            base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("Data must be valid base64 encoded string")
        return v


class AudioContent(BaseModel):
    type: str = "audio"
    data: str  # Base64-encoded audio data
    mimeType: str
    annotations: Optional[Dict[str, Any]] = None

    @field_validator("data")
    @classmethod
    def validate_base64_data(cls, v):
        try:
            base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("Data must be valid base64 encoded string")
        return v


class ResourceLinkContent(BaseModel):
    type: str = "resource_link"
    uri: str
    name: Optional[str] = None
    description: Optional[str] = None
    mimeType: Optional[str] = None
    annotations: Optional[Dict[str, Any]] = None


class EmbeddedResource(BaseModel):
    type: str = "resource"
    resource: Union[TextContentSchema, BinaryContentSchema]


class ContentSchema(BaseModel):
    content: Optional[List[dict]] = None
    structuredContent: Optional[dict] = None
