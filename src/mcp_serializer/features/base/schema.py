from pydantic import BaseModel
from typing import Optional
from enum import Enum
import json


class JsonSchemaTypes(Enum):
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"

    @classmethod
    def from_python_type(cls, python_type):
        if python_type is str:
            return cls.STRING
        if python_type is int:
            return cls.INTEGER
        if python_type is float:
            return cls.NUMBER
        if python_type is bool:
            return cls.BOOLEAN
        if python_type is list:
            return cls.ARRAY
        if python_type is dict:
            return cls.OBJECT
        if python_type is type(None):
            return cls.NULL
        raise ValueError(f"Unknown type for json schema: {python_type}")

    @classmethod
    def cast_python_type(cls, value, python_type):
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
        prop_type: JsonSchemaTypes,
        description: Optional[str] = None,
        required: bool = False,
    ):
        property_def = {"type": prop_type.value}
        if description:
            property_def["description"] = description

        self.properties[name] = property_def

        if required:
            self.required.append(name)

        return self
