import pytest
from mcp_serializer.features.tool.container import ToolsContainer, ToolRegistry
from mcp_serializer.features.tool.contents import ToolsContent
from mcp_serializer.features.base.container import FeatureContainer
from mcp_serializer.features.base.parsers import FunctionParser


class TestToolRegistry:
    def test_init(self):
        def sample_func():
            return "test"

        metadata = FunctionParser(sample_func).function_metadata
        registry = ToolRegistry(metadata, {"name": "test"})

        assert registry.metadata == metadata
        assert registry.extra == {"name": "test"}

    def test_init_without_extra(self):
        def sample_func():
            return "test"

        metadata = FunctionParser(sample_func).function_metadata
        registry = ToolRegistry(metadata)

        assert registry.extra == {}


class TestToolsContainer:
    def setup_method(self):
        self.container = ToolsContainer()

    def test_init(self):
        assert self.container.registrations == {}
        assert hasattr(self.container, "schema_assembler")

    def test_register_function(self):
        def sample_func():
            """Sample function"""
            return "test"

        metadata = self.container.register(sample_func, name="test_tool")

        assert metadata.name == "sample_func"
        assert "sample_func" in self.container.registrations
        assert isinstance(self.container.registrations["sample_func"], ToolRegistry)

    def test_register_function_with_parameters(self):
        def sample_func(param: str, count: int = 5):
            """Function with parameters"""
            return f"{param} x {count}"

        metadata = self.container.register(sample_func, name="param_tool")

        assert metadata.name == "sample_func"
        assert len(metadata.arguments) == 2
        assert "sample_func" in self.container.registrations

    def test_call_function_success(self):
        def sample_func():
            """Sample function"""
            content = ToolsContent()
            content.add_text("Function executed")
            return content

        self.container.register(sample_func)
        result = self.container.call("sample_func")

        assert "content" in result
        assert len(result["content"]) == 1

    def test_call_function_with_parameters(self):
        def greet_func(name: str, times: int = 1):
            """Greeting function"""
            content = ToolsContent()
            content.add_text(f"Hello {name}! " * times)
            return content

        self.container.register(greet_func)
        result = self.container.call("greet_func", name="World", times=2)

        assert "content" in result
        assert "Hello World! Hello World! " in str(result)

    def test_call_function_not_found(self):
        with pytest.raises(FeatureContainer.RegistryNotFound):
            self.container.call("nonexistent_func")

    def test_call_function_invalid_parameters(self):
        def sample_func(required_param: str):
            """Function with required parameter"""
            return ToolsContent()

        self.container.register(sample_func)

        with pytest.raises(FeatureContainer.RequiredParameterNotFound):
            self.container.call("sample_func")  # Missing required parameter

    def test_call_function_wrong_parameter_type(self):
        def sample_func(number: int):
            """Function expecting int"""
            return ToolsContent()

        self.container.register(sample_func)

        with pytest.raises(FeatureContainer.ParameterTypeCastingError):
            self.container.call("sample_func", number="not_a_number")

    def test_build_list_result_schema(self):
        def sample_func():
            """Sample function"""
            return ToolsContent()

        self.container.register(sample_func, name="test_tool")
        result = self.container.schema_assembler.build_list_result_schema()

        assert "tools" in result
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "test_tool"

    def test_multiple_function_registration(self):
        def func1():
            """First function"""
            return ToolsContent()

        def func2():
            """Second function"""
            return ToolsContent()

        self.container.register(func1, name="tool1")
        self.container.register(func2, name="tool2")

        assert len(self.container.registrations) == 2
        assert "func1" in self.container.registrations
        assert "func2" in self.container.registrations

        result = self.container.schema_assembler.build_list_result_schema()
        assert len(result["tools"]) == 2

    def test_function_with_return_annotation(self):
        def typed_func() -> str:
            """Function with return type annotation"""
            content = ToolsContent()
            content.add_text("Typed response")
            return content

        metadata = self.container.register(typed_func)
        assert metadata.return_type == str

    def test_call_function_execution_error(self):
        def error_func():
            """Function that raises an error"""
            raise RuntimeError("Function error")

        self.container.register(error_func)

        with pytest.raises(FeatureContainer.FunctionCallError):
            self.container.call("error_func")
