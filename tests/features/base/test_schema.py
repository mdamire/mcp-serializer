import pytest
from typing import List, Dict, Set, Tuple, Optional, Union, Any
from decimal import Decimal
from datetime import datetime, date, time, timedelta
from uuid import UUID
from pathlib import Path
from enum import Enum
from pydantic import BaseModel
from mcp_serializer.features.base.schema import JsonSchema, cast_python_type


class TestJsonSchema:
    """Tests for JsonSchema class."""

    def test_add_property_basic(self):
        """Test adding a basic string property."""
        schema = JsonSchema()
        result = schema.add_property(name="name", type_hint=str, required=False)

        assert result == schema
        assert schema.properties["name"]["type"] == "string"
        assert "name" not in schema.required

    def test_add_property_with_description_and_required(self):
        """Test adding a property with description and required flag."""
        schema = JsonSchema()
        schema.add_property(
            name="email",
            type_hint=str,
            description="User email",
            required=True,
        )

        assert schema.properties["email"]["type"] == "string"
        assert schema.properties["email"]["description"] == "User email"
        assert "email" in schema.required

    def test_add_property_chaining(self):
        """Test method chaining with add_property."""
        schema = JsonSchema()
        result = schema.add_property(
            name="name", type_hint=str, required=True
        ).add_property(name="age", type_hint=int, required=False)

        assert result == schema
        assert len(schema.properties) == 2
        assert "name" in schema.required
        assert "age" not in schema.required

    def test_add_property_with_default(self):
        """Test adding a property with a default value."""
        schema = JsonSchema()
        schema.add_property(
            name="count",
            type_hint=int,
            required=False,
            default=10,
            has_default=True,
        )

        assert schema.properties["count"]["type"] == "integer"
        assert schema.properties["count"]["default"] == 10
        assert "count" not in schema.required

    def test_add_property_with_none_default(self):
        """Test adding a property with None as default value."""
        schema = JsonSchema()
        schema.add_property(
            name="optional_field",
            type_hint=str,
            required=False,
            default=None,
            has_default=True,
        )

        assert schema.properties["optional_field"]["type"] == "string"
        assert schema.properties["optional_field"]["default"] is None
        assert "optional_field" not in schema.required

    def test_add_property_required_no_default(self):
        """Test adding a required property without default."""
        schema = JsonSchema()
        schema.add_property(
            name="username",
            type_hint=str,
            description="The user's name",
            required=True,
            has_default=False,
        )

        assert schema.properties["username"]["type"] == "string"
        assert schema.properties["username"]["description"] == "The user's name"
        assert "username" in schema.required
        assert "default" not in schema.properties["username"]

    def test_add_property_optional_type(self):
        """Test adding a property with Optional type."""
        schema = JsonSchema()
        schema.add_property(
            name="email",
            type_hint=Optional[str],
            description="User email address",
            required=False,
        )

        assert schema.properties["email"]["type"] == "string"
        assert "email" not in schema.required

    def test_add_property_list_type(self):
        """Test adding a property with List type."""
        schema = JsonSchema()
        schema.add_property(
            name="tags",
            type_hint=List[str],
            required=False,
            default=[],
            has_default=True,
        )

        assert schema.properties["tags"]["type"] == "array"
        assert schema.properties["tags"]["items"] == {"type": "string"}
        assert schema.properties["tags"]["default"] == []

    def test_add_property_dict_type(self):
        """Test adding a property with Dict type."""
        schema = JsonSchema()
        schema.add_property(
            name="metadata",
            type_hint=Dict[str, int],
            required=False,
            default={},
            has_default=True,
        )

        assert schema.properties["metadata"]["type"] == "object"
        assert schema.properties["metadata"]["additionalProperties"] == {
            "type": "integer"
        }
        assert schema.properties["metadata"]["default"] == {}

    def test_add_property_datetime_type(self):
        """Test adding a property with datetime type."""
        schema = JsonSchema()
        schema.add_property(
            name="created_at",
            type_hint=datetime,
            required=True,
        )

        assert schema.properties["created_at"]["type"] == "string"
        assert schema.properties["created_at"]["format"] == "date-time"


class TestJsonSchemaPythonTypeToJsonSchema:
    """Tests for _python_type_to_json_schema method."""

    def test_basic_types(self):
        """Test basic Python types conversion."""
        schema = JsonSchema()

        assert schema._python_type_to_json_schema(str) == {"type": "string"}
        assert schema._python_type_to_json_schema(int) == {"type": "integer"}
        assert schema._python_type_to_json_schema(float) == {"type": "number"}
        assert schema._python_type_to_json_schema(bool) == {"type": "boolean"}
        assert schema._python_type_to_json_schema(list) == {"type": "array"}
        assert schema._python_type_to_json_schema(dict) == {"type": "object"}

    def test_none_type(self):
        """Test None type conversion."""
        schema = JsonSchema()

        assert schema._python_type_to_json_schema(None) == {"type": "null"}
        assert schema._python_type_to_json_schema(type(None)) == {"type": "null"}

    def test_any_type(self):
        """Test Any type returns empty schema."""
        schema = JsonSchema()

        assert schema._python_type_to_json_schema(Any) == {}

    def test_optional_type(self):
        """Test Optional[X] returns schema for X."""
        schema = JsonSchema()

        assert schema._python_type_to_json_schema(Optional[str]) == {"type": "string"}
        assert schema._python_type_to_json_schema(Optional[int]) == {"type": "integer"}

    def test_union_type(self):
        """Test Union types."""
        schema = JsonSchema()

        # Union with None (Optional-like)
        assert schema._python_type_to_json_schema(Union[str, None]) == {
            "type": "string"
        }

        # Union of multiple types uses anyOf
        result = schema._python_type_to_json_schema(Union[str, int])
        assert "anyOf" in result
        assert {"type": "string"} in result["anyOf"]
        assert {"type": "integer"} in result["anyOf"]

    def test_list_type(self):
        """Test List types."""
        schema = JsonSchema()

        assert schema._python_type_to_json_schema(List[str]) == {
            "type": "array",
            "items": {"type": "string"},
        }
        assert schema._python_type_to_json_schema(List[int]) == {
            "type": "array",
            "items": {"type": "integer"},
        }

    def test_dict_type(self):
        """Test Dict types."""
        schema = JsonSchema()

        assert schema._python_type_to_json_schema(Dict[str, int]) == {
            "type": "object",
            "additionalProperties": {"type": "integer"},
        }

    def test_set_type(self):
        """Test Set types."""
        schema = JsonSchema()

        result = schema._python_type_to_json_schema(Set[str])
        assert result["type"] == "array"
        assert result["uniqueItems"] == True
        assert result["items"] == {"type": "string"}

    def test_tuple_type(self):
        """Test Tuple types."""
        schema = JsonSchema()

        # Fixed length tuple
        result = schema._python_type_to_json_schema(Tuple[str, int])
        assert result["type"] == "array"
        assert result["prefixItems"] == [{"type": "string"}, {"type": "integer"}]
        assert result["minItems"] == 2
        assert result["maxItems"] == 2

    def test_collection_types_without_params(self):
        """Test collection types without type parameters."""
        schema = JsonSchema()

        assert schema._python_type_to_json_schema(tuple) == {"type": "array"}
        assert schema._python_type_to_json_schema(set) == {"type": "array"}
        assert schema._python_type_to_json_schema(frozenset) == {"type": "array"}

    def test_bytes_type(self):
        """Test bytes types."""
        schema = JsonSchema()

        assert schema._python_type_to_json_schema(bytes) == {
            "type": "string",
            "contentEncoding": "base64",
        }
        assert schema._python_type_to_json_schema(bytearray) == {
            "type": "string",
            "contentEncoding": "base64",
        }

    def test_numeric_types(self):
        """Test numeric types."""
        schema = JsonSchema()

        assert schema._python_type_to_json_schema(Decimal) == {"type": "number"}
        assert schema._python_type_to_json_schema(complex) == {"type": "string"}

    def test_datetime_types(self):
        """Test datetime types."""
        schema = JsonSchema()

        assert schema._python_type_to_json_schema(datetime) == {
            "type": "string",
            "format": "date-time",
        }
        assert schema._python_type_to_json_schema(date) == {
            "type": "string",
            "format": "date",
        }
        assert schema._python_type_to_json_schema(time) == {
            "type": "string",
            "format": "time",
        }
        assert schema._python_type_to_json_schema(timedelta) == {"type": "string"}

    def test_uuid_type(self):
        """Test UUID type."""
        schema = JsonSchema()

        assert schema._python_type_to_json_schema(UUID) == {
            "type": "string",
            "format": "uuid",
        }

    def test_path_type(self):
        """Test Path type."""
        schema = JsonSchema()

        assert schema._python_type_to_json_schema(Path) == {"type": "string"}

    def test_enum_type(self):
        """Test Enum types."""
        schema = JsonSchema()

        class Color(Enum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"

        result = schema._python_type_to_json_schema(Color)
        assert result["type"] == "string"
        assert result["enum"] == ["red", "green", "blue"]

    def test_enum_int_values(self):
        """Test Enum with integer values."""
        schema = JsonSchema()

        class Priority(Enum):
            LOW = 1
            MEDIUM = 2
            HIGH = 3

        result = schema._python_type_to_json_schema(Priority)
        assert result["type"] == "integer"
        assert result["enum"] == [1, 2, 3]

    def test_pydantic_model(self):
        """Test Pydantic BaseModel types."""
        schema = JsonSchema()

        class UserModel(BaseModel):
            name: str
            age: int

        result = schema._python_type_to_json_schema(UserModel)
        # Should return the model's JSON schema
        assert "properties" in result
        assert "name" in result["properties"]
        assert "age" in result["properties"]

    def test_custom_class(self):
        """Test custom class types return object."""
        schema = JsonSchema()

        class CustomType:
            pass

        assert schema._python_type_to_json_schema(CustomType) == {"type": "object"}

    def test_nested_types(self):
        """Test nested complex types."""
        schema = JsonSchema()

        # List of Lists
        result = schema._python_type_to_json_schema(List[List[str]])
        assert result["type"] == "array"
        assert result["items"]["type"] == "array"
        assert result["items"]["items"] == {"type": "string"}

        # Dict with List values
        result = schema._python_type_to_json_schema(Dict[str, List[int]])
        assert result["type"] == "object"
        assert result["additionalProperties"]["type"] == "array"
        assert result["additionalProperties"]["items"] == {"type": "integer"}


class TestCastPythonType:
    """Tests for cast_python_type function."""

    def test_basic_types(self):
        """Test casting basic Python types."""
        assert cast_python_type("hello", str) == "hello"
        assert cast_python_type("42", int) == 42
        assert cast_python_type("3.14", float) == 3.14
        assert cast_python_type("true", bool) == True
        assert cast_python_type("false", bool) == False
        assert cast_python_type(1, bool) == True
        assert cast_python_type(0, bool) == False

    def test_none_type(self):
        """Test casting to None type."""
        assert cast_python_type(None, type(None)) is None
        assert cast_python_type("null", type(None)) is None

    def test_optional_type(self):
        """Test casting Optional types."""
        assert cast_python_type("hello", Optional[str]) == "hello"
        assert cast_python_type(None, Optional[str]) is None
        assert cast_python_type("42", Optional[int]) == 42

    def test_union_type(self):
        """Test casting Union types."""
        assert cast_python_type("hello", Union[str, int]) == "hello"
        assert cast_python_type("42", Union[str, int]) == "42"  # str takes precedence?
        # Actually, since it tries str first and succeeds, it returns str
        assert cast_python_type(42, Union[str, int]) == 42

    def test_list_type(self):
        """Test casting List types."""
        assert cast_python_type('["a", "b"]', List[str]) == ["a", "b"]
        assert cast_python_type(["1", "2"], List[int]) == [1, 2]
        assert cast_python_type("single", List[str]) == ["single"]

    def test_dict_type(self):
        """Test casting Dict types."""
        assert cast_python_type('{"a": 1}', Dict[str, int]) == {"a": 1}
        assert cast_python_type({"a": "1"}, Dict[str, int]) == {"a": 1}

    def test_set_type(self):
        """Test casting Set types."""
        result = cast_python_type(["a", "b", "a"], Set[str])
        assert isinstance(result, set)
        assert result == {"a", "b"}

    def test_tuple_type(self):
        """Test casting Tuple types."""
        assert cast_python_type(["a", "b"], Tuple[str, str]) == ("a", "b")
        assert cast_python_type(["a", "b", "c"], Tuple[str, ...]) == ("a", "b", "c")

    def test_datetime_types(self):
        """Test casting datetime types."""
        dt_str = "2023-01-01T12:00:00"
        dt = cast_python_type(dt_str, datetime)
        assert isinstance(dt, datetime)
        assert dt.isoformat() == dt_str

        date_str = "2023-01-01"
        d = cast_python_type(date_str, date)
        assert isinstance(d, date)
        assert d.isoformat() == date_str

    def test_uuid_type(self):
        """Test casting UUID type."""
        uuid_str = "12345678-1234-5678-9012-123456789012"
        uuid_obj = cast_python_type(uuid_str, UUID)
        assert isinstance(uuid_obj, UUID)
        assert str(uuid_obj) == uuid_str

    def test_path_type(self):
        """Test casting Path type."""
        path_str = "/home/user/file.txt"
        path_obj = cast_python_type(path_str, Path)
        assert isinstance(path_obj, Path)
        assert str(path_obj) == path_str

    def test_enum_type(self):
        """Test casting Enum types."""

        class Color(Enum):
            RED = "red"
            BLUE = "blue"

        assert cast_python_type("red", Color) == Color.RED
        assert cast_python_type("blue", Color) == Color.BLUE

    def test_pydantic_model(self):
        """Test casting Pydantic BaseModel."""

        class User(BaseModel):
            name: str
            age: int

        user_dict = {"name": "John", "age": 30}
        user = cast_python_type(user_dict, User)
        assert isinstance(user, User)
        assert user.name == "John"
        assert user.age == 30

    def test_decimal_type(self):
        """Test casting Decimal type."""
        dec = cast_python_type("3.14", Decimal)
        assert isinstance(dec, Decimal)
        assert str(dec) == "3.14"

    def test_bytes_type(self):
        """Test casting bytes type."""
        import base64

        b64_str = base64.b64encode(b"hello").decode()
        result = cast_python_type(b64_str, bytes)
        assert result == b"hello"
