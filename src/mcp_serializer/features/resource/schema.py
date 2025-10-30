from pydantic import BaseModel, field_validator
from typing import Optional, List, Union
from enum import Enum
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class AnnotationSchema(BaseModel):
    class AudienceType(Enum):
        USER = "user"
        ASSISTANT = "assistant"

    audience: Optional[str] = None
    priority: Optional[float] = None
    lastModified: Optional[str] = None

    @field_validator("audience")
    @classmethod
    def validate_audience(cls, v):
        if v is not None:
            valid_values = [e.value for e in cls.AudienceType]
            if v not in valid_values:
                logger.error(
                    f"Invalid audience value '{v}'. Must be one of: {valid_values}"
                )
                return None
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)) or not (0.0 <= v <= 1.0):
                logger.error(
                    f"Invalid priority value '{v}'. Must be a float between 0.0 and 1.0"
                )
                return None
        return v

    @field_validator("lastModified")
    @classmethod
    def validate_last_modified(cls, v):
        if v is not None:
            if isinstance(v, datetime):
                return v.isoformat()

            if isinstance(v, str):
                try:
                    datetime.fromisoformat(v.replace("Z", "+00:00"))
                    return v
                except ValueError:
                    logger.error(
                        f"Invalid ISO 8601 timestamp '{v}'. Using current timestamp."
                    )
                    return None
        return v


class ResourceDefinitionSchema(BaseModel):
    uri: str
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    mimeType: Optional[str] = None
    size: Optional[int] = None
    annotations: Optional[AnnotationSchema] = None


class ResourceListResultSchema(BaseModel):
    resources: List[ResourceDefinitionSchema]
    nextCursor: Optional[str] = None


class ResourceTemplateListResultSchema(BaseModel):
    resourceTemplates: List[ResourceDefinitionSchema]
    nextCursor: Optional[str] = None


class BaseContentSchema(BaseModel):
    uri: Optional[str] = None
    mimeType: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    annotations: Optional[AnnotationSchema] = None


class TextContentSchema(BaseContentSchema):
    text: str


class BinaryContentSchema(BaseContentSchema):
    blob: str


class ResultSchema(BaseModel):
    contents: List[Union[TextContentSchema, BinaryContentSchema]]
