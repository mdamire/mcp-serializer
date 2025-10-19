import pytest
from pydantic import BaseModel, Field
from mcp_serializer.features.tool.assembler import ToolsSchemaAssembler
from mcp_serializer.features.tool.container import ToolRegistry
from mcp_serializer.features.tool.result import ToolsResult
from mcp_serializer.features.base.parsers import FunctionParser
from mcp_serializer.features.base.assembler import FeatureSchemaAssembler


class SampleResponse(BaseModel):
    message: str = Field(description="Response message")
    status: int = Field(description="Status code")


class TestToolsSchemaAssembler:
    def setup_method(self):
        self.assembler = ToolsSchemaAssembler()

    def test_init(self):
        assert self.assembler.tools_list == []

    def test_add_tool_registry_basic(self):
        def sample_func():
            """Sample function"""
            return "test"

        metadata = FunctionParser(sample_func).function_metadata
        registry = ToolRegistry(metadata, {"name": "test_tool"})

        result = self.assembler.add_tool_registry(registry)

        assert len(self.assembler.tools_list) == 1
        assert result.name == "test_tool"
        assert result.title == "Sample function"

    def test_add_tool_registry_with_input_schema(self):
        def sample_func(param: str, count: int = 5):
            """Function with parameters"""
            return f"{param} x {count}"

        metadata = FunctionParser(sample_func).function_metadata
        registry = ToolRegistry(metadata)

        result = self.assembler.add_tool_registry(registry)

        assert result.inputSchema is not None
        assert len(self.assembler.tools_list) == 1

    def test_add_tool_registry_with_output_schema(self):
        def sample_func() -> SampleResponse:
            """Function with Pydantic return type"""
            return SampleResponse(message="test", status=200)

        metadata = FunctionParser(sample_func).function_metadata
        registry = ToolRegistry(metadata)

        result = self.assembler.add_tool_registry(registry)

        assert result.outputSchema is not None
        assert len(self.assembler.tools_list) == 1

    def test_create_input_schema_no_arguments(self):
        def sample_func():
            return "test"

        metadata = FunctionParser(sample_func).function_metadata
        input_schema = self.assembler._create_input_schema(metadata)

        assert input_schema is None

    def test_create_input_schema_with_arguments(self):
        def sample_func(name: str, age: int, active: bool = True):
            return f"{name} is {age}"

        metadata = FunctionParser(sample_func).function_metadata
        input_schema = self.assembler._create_input_schema(metadata)

        assert input_schema is not None
        schema_dict = input_schema.model_dump()
        assert "name" in schema_dict["properties"]
        assert "age" in schema_dict["properties"]
        assert "active" in schema_dict["properties"]

    def test_create_output_schema_no_return_type(self):
        def sample_func():
            return "test"

        metadata = FunctionParser(sample_func).function_metadata
        output_schema = self.assembler._create_output_schema(metadata)

        assert output_schema is None

    def test_create_output_schema_with_pydantic_model(self):
        def sample_func() -> SampleResponse:
            return SampleResponse(message="test", status=200)

        metadata = FunctionParser(sample_func).function_metadata
        output_schema = self.assembler._create_output_schema(metadata)

        assert output_schema is not None
        schema_dict = output_schema.model_dump()
        assert "message" in schema_dict["properties"]
        assert "status" in schema_dict["properties"]

    def test_build_list_result_schema(self):
        def sample_func():
            return "test"

        metadata = FunctionParser(sample_func).function_metadata
        registry = ToolRegistry(metadata, {"name": "test_tool"})
        self.assembler.add_tool_registry(registry)

        result = self.assembler.build_list_result_schema()

        assert "tools" in result
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "test_tool"

    def test_build_list_result_schema_pagination(self):
        # Add multiple tools to test pagination
        for i in range(15):

            def sample_func():
                return "test"

            metadata = FunctionParser(sample_func).function_metadata
            registry = ToolRegistry(metadata, {"name": f"tool{i}"})
            self.assembler.add_tool_registry(registry)

        result = self.assembler.build_list_result_schema(page_size=10)

        assert "tools" in result
        assert len(result["tools"]) == 10  # Page size limit
        assert "nextCursor" in result
        assert result["nextCursor"] is not None

    def test_build_list_result_schema_with_cursor(self):
        # Add multiple tools
        for i in range(12):

            def sample_func():
                return "test"

            metadata = FunctionParser(sample_func).function_metadata
            registry = ToolRegistry(metadata, {"name": f"tool{i}"})
            self.assembler.add_tool_registry(registry)

        # Get first page
        first_page = self.assembler.build_list_result_schema(page_size=10)
        next_cursor = first_page["nextCursor"]

        # Get second page with cursor
        second_page = self.assembler.build_list_result_schema(
            page_size=10, cursor=next_cursor
        )

        assert "tools" in second_page
        assert len(second_page["tools"]) == 2  # Remaining items
        assert second_page.get("nextCursor") is None  # No more pages

    def test_process_result_tools_content(self):
        tools_result = ToolsResult()
        tools_result.add_text_content("Test response")

        result = self.assembler.process_result(tools_result)

        assert "content" in result
        assert len(result["content"]) == 1

    def test_process_result_pydantic_model(self):
        sample_response = SampleResponse(message="test", status=200)

        result = self.assembler.process_result(sample_response)

        assert "structuredContent" in result
        assert result["structuredContent"]["message"] == "test"
        assert result["structuredContent"]["status"] == 200

    def test_process_result_unsupported_type(self):
        with pytest.raises(FeatureSchemaAssembler.UnsupportedResultTypeError):
            self.assembler.process_result("invalid_content")
