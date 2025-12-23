from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any, List, Union
from ..resource.schema import TextContentSchema, BinaryContentSchema
import base64


class ArgumentSchema(BaseModel):
    name: str
    description: Optional[str] = None
    required: bool = True


class PromptDefinitionSchema(BaseModel):
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    arguments: Optional[List[ArgumentSchema]] = None


class PromptsListSchema(BaseModel):
    prompts: List[dict]
    nextCursor: Optional[str] = None


# 'Getting a prompt' schema classes
class TextContent(BaseModel):
    type: str = "text"
    text: str
    mimeType: Optional[str] = None
    annotations: Optional[Dict[str, Any]] = None


class ImageContent(BaseModel):
    type: str = "image"
    data: str
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
    data: str
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


class EmbeddedResource(BaseModel):
    type: str = "resource"
    resource: Union[TextContentSchema, BinaryContentSchema]


class PromptMessageSchema(BaseModel):
    role: str
    content: dict

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ["user", "assistant"]:
            raise ValueError("Role must be either 'user' or 'assistant'")
        return v


class PromptResultSchema(BaseModel):
    description: Optional[str] = None
    messages: List[dict]
