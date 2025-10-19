import pytest
from mcp_serializer.features.resource.container import (
    ResourceContainer,
    ResultRegistry,
    FunctionRegistry,
)
from mcp_serializer.features.resource.result import ResourceResult
from mcp_serializer.features.base.container import FeatureContainer


class TestResultRegistry:
    def test_init(self):
        result = ResourceResult()
        registry = ResultRegistry(result, "file://test.txt", {"name": "test"})

        assert registry.result == result
        assert registry.uri == "file://test.txt"
        assert registry.extra == {"name": "test"}

    def test_init_without_extra(self):
        result = ResourceResult()
        registry = ResultRegistry(result, "file://test.txt")

        assert registry.extra == {}


class TestFunctionRegistry:
    def test_init(self):
        def sample_func():
            return "test"

        from mcp_serializer.features.base.parsers import FunctionParser

        metadata = FunctionParser(sample_func).function_metadata
        registry = FunctionRegistry(metadata, "file://test.txt", {"name": "test"})

        assert registry.metadata == metadata
        assert registry.uri == "file://test.txt"
        assert registry.extra == {"name": "test"}

    def test_init_without_extra(self):
        def sample_func():
            return "test"

        from mcp_serializer.features.base.parsers import FunctionParser

        metadata = FunctionParser(sample_func).function_metadata
        registry = FunctionRegistry(metadata, "file://test.txt")

        assert registry.extra == {}


class TestResourceContainer:
    def setup_method(self):
        self.container = ResourceContainer()

    def test_init(self):
        assert self.container.registrations == {}
        assert hasattr(self.container, "schema_assembler")

    def test_add_resource_success(self):
        result = ResourceResult()
        result.add_text_content("Hello", "text/plain")

        registry = self.container.add_resource("file://test.txt", result, name="test")

        assert isinstance(registry, ResultRegistry)
        assert registry.uri == "file://test.txt"
        assert "file://test.txt" in self.container.registrations

    def test_add_resource_invalid_content(self):
        with pytest.raises(ValueError, match="Content must be a ResourceResult object"):
            self.container.add_resource("file://test.txt", "invalid_content")

    def test_register_function(self):
        def sample_func():
            """Sample function"""
            return "test"

        metadata = self.container.register(sample_func, "file://test.txt", name="test")

        assert metadata.name == "sample_func"
        assert "file://test.txt" in self.container.registrations
        assert isinstance(
            self.container.registrations["file://test.txt"], FunctionRegistry
        )

    def test_find_exact_match_success(self):
        def sample_func():
            return "test"

        self.container.register(sample_func, "file://test.txt")
        registry = self.container._find_exact_match("file://test.txt")

        assert registry is not None
        assert isinstance(registry, FunctionRegistry)
        assert registry.uri == "file://test.txt"

    def test_find_exact_match_with_trailing_slash(self):
        def sample_func():
            return "test"

        self.container.register(sample_func, "file://test.txt")
        registry = self.container._find_exact_match("file://test.txt/")

        assert registry is not None
        assert registry.uri == "file://test.txt"

    def test_find_exact_match_not_found(self):
        registry = self.container._find_exact_match("file://nonexistent.txt")
        assert registry is None

    def test_find_prefix_match_success(self):
        def sample_func():
            return "test"

        self.container.register(sample_func, "file://test")
        registry = self.container._find_prefix_match("file://test/param1")

        assert registry is not None
        assert registry.uri == "file://test"

    def test_find_prefix_match_not_found(self):
        registry = self.container._find_prefix_match("file://nonexistent")
        assert registry is None

    def test_extract_path_params_function_registry(self):
        def sample_func(param1: str, param2: str):
            return "test"

        self.container.register(sample_func, "file://test")
        registry = self.container.registrations["file://test"]

        params = self.container._extract_path_params(
            "file://test/value1/value2", registry
        )

        assert params == {"param1": "value1", "param2": "value2"}

    def test_extract_path_params_content_registry(self):
        result = ResourceResult()
        self.container.add_resource("file://test", result)
        registry = self.container.registrations["file://test"]

        params = self.container._extract_path_params("file://test/extra/path", registry)

        assert params == {}

    def test_get_registry_exact_match(self):
        def sample_func():
            return "test"

        self.container.register(sample_func, "file://test.txt")

        registry, params = self.container._get_registry("file://test.txt")

        assert isinstance(registry, FunctionRegistry)
        assert params == {}

    def test_get_registry_prefix_match_with_params(self):
        def sample_func(param: str):
            return "test"

        self.container.register(sample_func, "file://test")

        registry, params = self.container._get_registry("file://test/value1")

        assert isinstance(registry, FunctionRegistry)
        assert params == {"param": "value1"}

    def test_get_registry_not_found(self):
        with pytest.raises(FeatureContainer.RegistryNotFound):
            self.container._get_registry("file://nonexistent.txt")

    def test_call_content_registry(self):
        resource_result = ResourceResult()
        resource_result.add_text_content("Hello world", "text/plain")

        self.container.add_resource("file://test.txt", resource_result)
        result = self.container.call("file://test.txt")

        assert "contents" in result
        assert len(result["contents"]) == 1
        assert result["contents"][0]["text"] == "Hello world"

    def test_call_function_registry(self):
        def sample_func():
            resource_result = ResourceResult()
            resource_result.add_text_content("Generated content", "text/plain")
            return resource_result

        self.container.register(sample_func, "file://dynamic.txt")
        result = self.container.call("file://dynamic.txt")

        assert "contents" in result
        assert result["contents"][0]["text"] == "Generated content"

    def test_call_function_with_path_params(self):
        def sample_func(name: str):
            resource_result = ResourceResult()
            resource_result.add_text_content(f"Hello {name}", "text/plain")
            return resource_result

        self.container.register(sample_func, "file://greet")
        result = self.container.call("file://greet/world")

        assert "contents" in result
        assert result["contents"][0]["text"] == "Hello world"

    def test_build_list_result_schema(self):
        resource_result = ResourceResult()
        resource_result.add_text_content("Test", "text/plain")

        self.container.add_resource("file://test.txt", resource_result, name="test")
        result = self.container.schema_assembler.build_list_result_schema()

        assert "resources" in result
        assert len(result["resources"]) == 1

    def test_build_template_list_result_schema(self):
        def sample_func(param: str):
            resource_result = ResourceResult()
            resource_result.add_text_content(f"Hello {param}", "text/plain")
            return resource_result

        self.container.register(sample_func, "file://test")
        result = self.container.schema_assembler.build_template_list_result_schema()

        assert "resourceTemplates" in result
        assert len(result["resourceTemplates"]) == 1

    def test_add_http_resource_without_content(self):
        # HTTP URI without content should appear in list but not be callable
        registry = self.container.add_resource(
            "https://example.com/api/data", name="API Data"
        )

        assert registry.uri == "https://example.com/api/data"
        assert registry.result is None
        assert (
            "https://example.com/api/data" not in self.container.registrations
        )  # Not callable

        # Should appear in list schema
        result = self.container.schema_assembler.build_list_result_schema()
        assert "resources" in result
        assert len(result["resources"]) == 1
        assert result["resources"][0]["uri"] == "https://example.com/api/data"
        assert result["resources"][0]["name"] == "API Data"

        # Should raise RegistryNotFound when called
        with pytest.raises(FeatureContainer.RegistryNotFound):
            self.container.call("https://example.com/api/data")

    def test_add_http_resource_with_content(self):
        # HTTP URI with content should work normally
        resource_result = ResourceResult()
        resource_result.add_text_content("API response", "application/json")

        registry = self.container.add_resource(
            "https://example.com/api/data", resource_result, name="API Data"
        )

        assert registry.uri == "https://example.com/api/data"
        assert registry.result is not None
        assert (
            "https://example.com/api/data" in self.container.registrations
        )  # Is callable

        # Should be callable
        result = self.container.call("https://example.com/api/data")
        assert "contents" in result
        assert result["contents"][0]["text"] == "API response"
