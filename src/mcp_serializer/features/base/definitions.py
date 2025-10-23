from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass


class Empty:
    """Sentinel class to represent no default value."""

    def __repr__(self):
        return "Empty"


class ContentTypes:
    """Content type constants for file metadata."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"


@dataclass
class FileMetadata:
    """Metadata for a file."""

    size: int
    name: str
    mime_type: str
    data: Union[str, bytes]
    content_type: ContentTypes
    uri: Optional[str] = None


@dataclass
class ArgumentMetadata:
    """Metadata for a function argument."""

    name: str
    type_hint: type
    description: Optional[str] = None
    required: bool = True
    default: Any = None


@dataclass
class FunctionMetadata:
    """Container for all parsed function metadata."""

    empty = Empty()

    name: str = ""
    title: Optional[str] = None
    description: str = ""
    arguments: List[ArgumentMetadata] = None
    return_type: Optional[type] = None
    function: Any = None

    def __post_init__(self):
        if self.arguments is None:
            self.arguments = []

    @property
    def has_arguments(self):
        return len(self.arguments) > 0

    @property
    def has_required_arguments(self):
        return any(arg.required for arg in self.arguments)

    @property
    def has_optional_arguments(self):
        return any(not arg.required for arg in self.arguments)

    def to_dict(self) -> Dict[str, Any]:
        """Convert all parsed information to a dictionary."""
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "arguments": [
                {
                    "name": arg.name,
                    "type": arg.type_hint,
                    "description": arg.description,
                    "required": arg.required,
                    "default": arg.default,
                }
                for arg in self.arguments
            ],
            "return_type": self.return_type,
        }
