import pytest
from mcp_serializer.features.resource.assembler import ResourceSchemaAssembler
from mcp_serializer.features.resource.container import FunctionRegistry
from mcp_serializer.features.resource.contents import ResourceContent
from mcp_serializer.features.base.parsers import FunctionParser
from mcp_serializer.features.base.assembler import FeatureSchemaAssembler
from mcp_serializer.features.resource.schema import AnnotationSchema


class TestResourceSchemaAssembler:
    def setup_method(self):
        self.assembler = ResourceSchemaAssembler(10)

    def test_init(self):
        assert self.assembler.resource_list == []
        assert self.assembler.resource_template_list == []

    def test_add_resource_registry_without_required_args(self):
        def sample_func():
            return "test"

        registry = FunctionRegistry(
            FunctionParser(sample_func).function_metadata, "file://test.txt"
        )
        self.assembler.add_resource_registry(registry)

        assert len(self.assembler.resource_list) == 1
        assert len(self.assembler.resource_template_list) == 0
        assert self.assembler.resource_list[0] == registry

    def test_add_resource_registry_with_required_args(self):
        def sample_func(param: str):
            return f"test-{param}"

        registry = FunctionRegistry(
            FunctionParser(sample_func).function_metadata, "file://test-{param}.txt"
        )
        self.assembler.add_resource_registry(registry)

        assert len(self.assembler.resource_list) == 0
        assert len(self.assembler.resource_template_list) == 1
        assert self.assembler.resource_template_list[0] == registry

    def test_build_list_result_schema(self):
        def sample_func():
            return "test"

        registry = FunctionRegistry(
            FunctionParser(sample_func).function_metadata, "file://test.txt"
        )
        registry.extra = {"name": "test", "description": "Test resource"}
        self.assembler.add_resource_registry(registry)

        result = self.assembler.build_list_result_schema()

        assert "resources" in result
        assert len(result["resources"]) == 1
        assert result["resources"][0]["uri"] == "file://test.txt"
        assert result["resources"][0]["name"] == "test"

    def test_build_template_list_result_schema(self):
        def sample_func(param: str):
            return f"test-{param}"

        registry = FunctionRegistry(
            FunctionParser(sample_func).function_metadata, "file://test"
        )
        registry.extra = {"name": "test-template"}
        self.assembler.add_resource_registry(registry)

        result = self.assembler.build_template_list_result_schema()

        assert "resourceTemplates" in result
        assert len(result["resourceTemplates"]) == 1
        assert result["resourceTemplates"][0]["uri"] == "file://test/{param}"

    def test_process_content_text(self):
        def sample_func():
            return "test"

        registry = FunctionRegistry(sample_func, "file://test.txt")
        registry.extra = {"name": "test-file"}

        resource_content = ResourceContent()
        resource_content.add_text_content(text="Hello world", mime_type="text/plain")

        result = self.assembler.process_content(resource_content, registry)

        assert "contents" in result
        assert len(result["contents"]) == 1
        assert result["contents"][0]["text"] == "Hello world"
        assert result["contents"][0]["mimeType"] == "text/plain"
        assert result["contents"][0]["name"] == "test-file"

    def test_process_content_binary(self):
        def sample_func():
            return "test"

        registry = FunctionRegistry(sample_func, "file://test.bin")
        annotation = AnnotationSchema(
            audience="user", priority=0.5, lastModified="2021-01-01T00:00:00Z"
        )
        registry.extra = {"annotations": annotation}

        resource_content = ResourceContent()
        resource_content.add_binary_content(
            blob="aGVsbG8=", mime_type="application/octet-stream"
        )

        result = self.assembler.process_content(resource_content, registry)

        assert "contents" in result
        assert len(result["contents"]) == 1
        assert result["contents"][0]["blob"] == "aGVsbG8="
        assert result["contents"][0]["mimeType"] == "application/octet-stream"
        assert result["contents"][0]["annotations"] == annotation.model_dump()

    def test_process_content_unsupported_type(self):
        def sample_func():
            return "test"

        registry = FunctionRegistry(sample_func, "file://test.txt")

        with pytest.raises(FeatureSchemaAssembler.UnsupportedResultTypeError):
            self.assembler.process_content("invalid_content", registry)

    def test_pagination_no_cursor(self):
        # Add multiple resources to test pagination
        for i in range(15):  # More than page size (10)

            def sample_func():
                return "test"

            registry = FunctionRegistry(
                FunctionParser(sample_func).function_metadata, f"file://test{i}.txt"
            )
            registry.extra = {"name": f"test{i}"}
            self.assembler.add_resource_registry(registry)

        result = self.assembler.build_list_result_schema()

        assert "resources" in result
        assert len(result["resources"]) == 10  # Page size limit
        assert "nextCursor" in result
        assert result["nextCursor"] is not None  # Should have next cursor

    def test_pagination_with_cursor(self):
        # Add multiple resources
        for i in range(15):

            def sample_func():
                return "test"

            registry = FunctionRegistry(
                FunctionParser(sample_func).function_metadata, f"file://test{i}.txt"
            )
            self.assembler.add_resource_registry(registry)

        # Get first page
        first_page = self.assembler.build_list_result_schema()
        next_cursor = first_page["nextCursor"]

        # Get second page with cursor
        second_page = self.assembler.build_list_result_schema(cursor=next_cursor)

        assert "resources" in second_page
        assert len(second_page["resources"]) == 5  # Remaining items
        assert second_page.get("nextCursor") is None  # No more pages

    def test_pagination_all_items_fit_in_one_page(self):
        # Add fewer resources than page size
        for i in range(5):

            def sample_func():
                return "test"

            registry = FunctionRegistry(
                FunctionParser(sample_func).function_metadata, f"file://test{i}.txt"
            )
            self.assembler.add_resource_registry(registry)

        result = self.assembler.build_list_result_schema()

        assert "resources" in result
        assert len(result["resources"]) == 5
        assert result.get("nextCursor") is None  # No pagination needed

    def test_template_pagination_no_cursor(self):
        # Add multiple template resources (functions with required args)
        for i in range(15):

            def sample_func(param: str):
                return f"test-{param}"

            registry = FunctionRegistry(
                FunctionParser(sample_func).function_metadata, f"file://template{i}"
            )
            registry.extra = {"name": f"template{i}"}
            self.assembler.add_resource_registry(registry)

        result = self.assembler.build_template_list_result_schema()

        assert "resourceTemplates" in result
        assert len(result["resourceTemplates"]) == 10  # Page size limit
        assert "nextCursor" in result
        assert result["nextCursor"] is not None  # Should have next cursor

    def test_template_pagination_with_cursor(self):
        # Add multiple template resources
        for i in range(12):

            def sample_func(param: str):
                return f"test-{param}"

            registry = FunctionRegistry(
                FunctionParser(sample_func).function_metadata, f"file://template{i}"
            )
            self.assembler.add_resource_registry(registry)

        # Get first page
        first_page = self.assembler.build_template_list_result_schema()
        next_cursor = first_page["nextCursor"]

        # Get second page with cursor
        second_page = self.assembler.build_template_list_result_schema(
            cursor=next_cursor
        )

        assert "resourceTemplates" in second_page
        assert len(second_page["resourceTemplates"]) == 2  # Remaining items
        assert second_page.get("nextCursor") is None  # No more pages
