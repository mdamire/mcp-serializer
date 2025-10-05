import pytest
from mcp_serializer.features.base.schema import JsonSchemaTypes, JsonSchema


class TestJsonSchemaTypes:
    def test_from_python_type_mappings(self):
        mappings = [
            (str, JsonSchemaTypes.STRING),
            (int, JsonSchemaTypes.INTEGER),
            (float, JsonSchemaTypes.NUMBER),
            (bool, JsonSchemaTypes.BOOLEAN),
            (list, JsonSchemaTypes.ARRAY),
            (dict, JsonSchemaTypes.OBJECT),
            (type(None), JsonSchemaTypes.NULL),
        ]

        for python_type, expected in mappings:
            assert JsonSchemaTypes.from_python_type(python_type) == expected

    def test_unknown_type(self):
        class CustomType:
            pass

        with pytest.raises(ValueError):
            JsonSchemaTypes.from_python_type(CustomType)


class TestJsonSchema:
    def test_add_property_basic(self):
        schema = JsonSchema()
        result = schema.add_property("name", JsonSchemaTypes.STRING)

        assert result == schema
        assert schema.properties["name"]["type"] == "string"
        assert "name" not in schema.required

    def test_add_property_with_description_and_required(self):
        schema = JsonSchema()
        schema.add_property(
            "email", JsonSchemaTypes.STRING, description="User email", required=True
        )

        assert schema.properties["email"]["type"] == "string"
        assert schema.properties["email"]["description"] == "User email"
        assert "email" in schema.required

    def test_add_property_chaining(self):
        schema = JsonSchema()
        result = schema.add_property(
            "name", JsonSchemaTypes.STRING, required=True
        ).add_property("age", JsonSchemaTypes.INTEGER)

        assert result == schema
        assert len(schema.properties) == 2
        assert "name" in schema.required
        assert "age" not in schema.required
