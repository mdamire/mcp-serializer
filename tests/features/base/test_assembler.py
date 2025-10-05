from unittest.mock import Mock
from mcp_serializer.features.base.assembler import FeatureSchemaAssembler


def test_build_non_none_dict():
    """Test _build_non_none_dict filters out None values."""
    assembler = FeatureSchemaAssembler()

    # Create a mock schema object with model_dump method
    mock_schema = Mock()
    mock_schema.model_dump.return_value = {
        "name": "test",
        "value": 42,
        "optional": None,
        "description": "test description",
        "empty_list": [],
        "none_field": None,
    }

    result = assembler._build_non_none_dict(mock_schema)

    expected = {
        "name": "test",
        "value": 42,
        "description": "test description",
        "empty_list": [],
    }

    assert result == expected
    assert "optional" not in result
    assert "none_field" not in result


def test_append_sorted_list():
    """Test _append_sorted_list adds and sorts items by key."""
    assembler = FeatureSchemaAssembler()

    # Test with dictionary objects
    target_list = [{"name": "b", "value": 2}, {"name": "d", "value": 4}]
    new_obj = {"name": "a", "value": 1}

    assembler._append_sorted_list(target_list, new_obj, "name")

    expected = [
        {"name": "a", "value": 1},
        {"name": "b", "value": 2},
        {"name": "d", "value": 4},
    ]

    assert target_list == expected

    # Test with object attributes
    class TestObj:
        def __init__(self, name, value):
            self.name = name
            self.value = value

        def __eq__(self, other):
            return self.name == other.name and self.value == other.value

    obj_list = [TestObj("c", 3), TestObj("a", 1)]
    new_obj = TestObj("b", 2)

    assembler._append_sorted_list(obj_list, new_obj, "name")

    assert len(obj_list) == 3
    assert obj_list[0].name == "a"
    assert obj_list[1].name == "b"
    assert obj_list[2].name == "c"
