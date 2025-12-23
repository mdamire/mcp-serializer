from pydantic import BaseModel
from typing import Optional, get_origin, get_args, Union, Any
from enum import Enum
from decimal import Decimal
from datetime import datetime, date, time, timedelta
from uuid import UUID
from pathlib import Path
import typing
import json


def cast_python_type(value, python_type):
    """
    Cast a value to the specified Python type.
    
    Args:
        value: The value to cast
        python_type: The target Python type
        
    Returns:
        The value cast to the specified type
    """
    if type(value) == python_type:
        return value

    if type(value) is str and value.lower() == "null":
        return None
    if python_type is bool:
        if value.lower() in ("true", "1", "yes", "on"):
            return True
        elif value.lower() in ("false", "0", "no", "off"):
            return False
        return bool(value)
    if python_type in (list, dict) and isinstance(value, str):
        return json.loads(value)
    return python_type(value)


class JsonSchema(BaseModel):
    type: str = "object"
    properties: dict = {}
    required: list[str] = []

    def add_property(
        self,
        name: str,
        type_hint,
        description: Optional[str] = None,
        required: bool = True,
        default: Any = None,
        has_default: bool = False,
    ):
        """
        Add a property to the JSON schema.

        Args:
            name: Property name
            type_hint: Python type hint for the property
            description: Optional description of the property
            required: Whether the property is required
            default: Default value for the property
            has_default: Whether a default value was provided (needed to distinguish None as default vs no default)

        Returns:
            self for method chaining
        """
        property_def = self._python_type_to_json_schema(type_hint)

        if description:
            property_def["description"] = description

        if has_default:
            property_def["default"] = default

        self.properties[name] = property_def

        if required:
            self.required.append(name)

        return self

    def _python_type_to_json_schema(self, python_type) -> dict:
        """
        Convert a Python type to a JSON Schema definition dict.

        Handles nested types like List[str], Dict[str, int], Optional[X], etc.
        """
        # Handle None type
        if python_type is None or python_type is type(None):
            return {"type": "null"}

        # Handle typing.Any
        if python_type is Any:
            return {}  # Empty schema accepts anything

        # Get the origin type for generic types
        origin = get_origin(python_type)
        args = get_args(python_type)

        # Handle Optional[X] which is Union[X, None]
        if origin is Union:
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                # Optional[X] - return schema for X
                return self._python_type_to_json_schema(non_none_args[0])
            elif len(non_none_args) == 0:
                return {"type": "null"}
            else:
                # Union of multiple types - use anyOf
                return {
                    "anyOf": [
                        self._python_type_to_json_schema(arg) for arg in non_none_args
                    ]
                }

        # Handle List[X], list[X]
        if origin in (list,) or (
            hasattr(typing, "List") and origin is getattr(typing, "List", None)
        ):
            schema = {"type": "array"}
            if args:
                schema["items"] = self._python_type_to_json_schema(args[0])
            return schema

        # Handle Dict[K, V], dict[K, V]
        if origin in (dict,) or (
            hasattr(typing, "Dict") and origin is getattr(typing, "Dict", None)
        ):
            schema = {"type": "object"}
            if args and len(args) >= 2:
                # additionalProperties describes the value type
                schema["additionalProperties"] = self._python_type_to_json_schema(
                    args[1]
                )
            return schema

        # Handle Set[X], set[X], FrozenSet[X]
        if (
            origin in (set, frozenset)
            or origin is getattr(typing, "Set", None)
            or origin is getattr(typing, "FrozenSet", None)
        ):
            schema = {"type": "array", "uniqueItems": True}
            if args:
                schema["items"] = self._python_type_to_json_schema(args[0])
            return schema

        # Handle Tuple[X, Y, ...]
        if origin in (tuple,) or origin is getattr(typing, "Tuple", None):
            schema = {"type": "array"}
            if args:
                # Check if it's Tuple[X, ...] (variable length)
                if len(args) == 2 and args[1] is Ellipsis:
                    schema["items"] = self._python_type_to_json_schema(args[0])
                else:
                    # Fixed length tuple with prefixItems
                    schema["prefixItems"] = [
                        self._python_type_to_json_schema(arg) for arg in args
                    ]
                    schema["minItems"] = len(args)
                    schema["maxItems"] = len(args)
            return schema

        # Handle basic Python types
        if python_type is str:
            return {"type": "string"}
        if python_type is int:
            return {"type": "integer"}
        if python_type is float:
            return {"type": "number"}
        if python_type is bool:
            return {"type": "boolean"}
        if python_type is list:
            return {"type": "array"}
        if python_type is dict:
            return {"type": "object"}

        # Handle tuple, set, frozenset without type params
        if python_type in (tuple, set, frozenset):
            return {"type": "array"}

        # Handle bytes as string (base64 encoded)
        if python_type in (bytes, bytearray):
            return {"type": "string", "contentEncoding": "base64"}

        # Handle numeric types
        if python_type is Decimal:
            return {"type": "number"}
        if python_type is complex:
            return {"type": "string"}

        # Handle date/time types as string with format
        if python_type is datetime:
            return {"type": "string", "format": "date-time"}
        if python_type is date:
            return {"type": "string", "format": "date"}
        if python_type is time:
            return {"type": "string", "format": "time"}
        if python_type is timedelta:
            return {"type": "string"}

        # Handle UUID as string with format
        if python_type is UUID:
            return {"type": "string", "format": "uuid"}

        # Handle Path as string
        if python_type is Path or (
            isinstance(python_type, type) and issubclass(python_type, Path)
        ):
            return {"type": "string"}

        # Handle Enum types - use enum values
        if isinstance(python_type, type) and issubclass(python_type, Enum):
            enum_values = [e.value for e in python_type]
            # Determine type from first value
            if enum_values:
                first_val = enum_values[0]
                if isinstance(first_val, str):
                    return {"type": "string", "enum": enum_values}
                elif isinstance(first_val, int):
                    return {"type": "integer", "enum": enum_values}
                elif isinstance(first_val, float):
                    return {"type": "number", "enum": enum_values}
            return {"type": "string", "enum": enum_values}

        # Handle Pydantic BaseModel - convert to object schema
        if isinstance(python_type, type) and issubclass(python_type, BaseModel):
            return python_type.model_json_schema()

        # Handle any other class type as object
        if isinstance(python_type, type):
            return {"type": "object"}

        # Handle string type hints (forward references)
        if isinstance(python_type, str):
            return {"type": "object"}

        # Default: return empty schema (accepts anything)
        return {}
