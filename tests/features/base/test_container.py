import pytest
from unittest.mock import Mock, patch
from mcp_serializer.features.base.container import FeatureContainer
from mcp_serializer.features.base.definitions import FunctionMetadata, ArgumentMetadata
from mcp_serializer.features.base.schema import JsonSchemaTypes


class TestFeatureContainer:
    def setup_method(self):
        self.container = FeatureContainer()

    def test_get_function_metadata(self):
        def sample_func(x: int):
            """Sample function"""
            return x

        result = self.container._get_function_metadata(sample_func)

        assert isinstance(result, FunctionMetadata)
        assert result.name == "sample_func"

    def test_get_registry_success(self):
        registrations = {"key1": "value1"}
        result = self.container._get_registry(registrations, "key1")
        assert result == "value1"

    def test_get_registry_not_found(self):
        registrations = {"key1": "value1"}

        with pytest.raises(FeatureContainer.RegistryNotFound) as exc_info:
            self.container._get_registry(registrations, "nonexistent")

        assert exc_info.value.key == "nonexistent"

    def test_call_function_success(self):
        def test_func(a, b):
            return a + b

        result = self.container._call_function(test_func, {"a": 1, "b": 2})
        assert result == 3

    def test_call_function_error(self):
        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(FeatureContainer.FunctionCallError) as exc_info:
            self.container._call_function(failing_func)

        assert exc_info.value.func_name == "failing_func"
        assert isinstance(exc_info.value.error, ValueError)

    def test_validate_parameters_success(self):
        arg1 = ArgumentMetadata(name="x", type_hint=int, required=True, default=None)
        func_metadata = FunctionMetadata(
            name="test_func",
            arguments=[arg1],
            description="Test function",
            return_type=int,
        )

        kwargs = {"x": "123"}

        with patch.object(JsonSchemaTypes, "cast_python_type", return_value=123):
            result = self.container._validate_parameters(func_metadata, kwargs)
            assert result == {"x": 123}

    def test_validate_parameters_missing_required(self):
        arg1 = ArgumentMetadata(
            name="required_param", type_hint=int, required=True, default=None
        )
        func_metadata = FunctionMetadata(
            name="test_func",
            arguments=[arg1],
            description="Test function",
            return_type=int,
        )

        with pytest.raises(FeatureContainer.RequiredParameterNotFound) as exc_info:
            self.container._validate_parameters(func_metadata, {})

        assert exc_info.value.param_name == "required_param"

    def test_validate_parameters_type_casting_error(self):
        arg1 = ArgumentMetadata(name="x", type_hint=int, required=True, default=None)
        func_metadata = FunctionMetadata(
            name="test_func",
            arguments=[arg1],
            description="Test function",
            return_type=int,
        )

        kwargs = {"x": "invalid"}

        with patch.object(
            JsonSchemaTypes, "cast_python_type", side_effect=ValueError("Invalid")
        ):
            with pytest.raises(FeatureContainer.ParameterTypeCastingError) as exc_info:
                self.container._validate_parameters(func_metadata, kwargs)

        assert exc_info.value.param_name == "x"
        assert exc_info.value.value == "invalid"
