import pytest
from mcp_serializer.features.prompt.assembler import PromptsSchemaAssembler
from mcp_serializer.features.prompt.container import PromptRegistry
from mcp_serializer.features.prompt.contents import PromptsContent
from mcp_serializer.features.base.parsers import FunctionParser
from mcp_serializer.features.base.assembler import FeatureSchemaAssembler


class TestPromptsSchemaAssembler:
    def setup_method(self):
        self.assembler = PromptsSchemaAssembler()

    def test_init_and_add_registry(self):
        def sample_prompt(name: str):
            """Sample prompt function"""
            content = PromptsContent()
            content.add_text(f"Hello {name}")
            return content

        metadata = FunctionParser(sample_prompt).function_metadata
        registry = PromptRegistry(metadata, {"name": "greeting_prompt"})

        result = self.assembler.add_registry(registry)

        assert len(self.assembler.prompts_list) == 1
        assert result.name == "greeting_prompt"
        assert result.title == "Sample prompt function"

    def test_create_arguments_schema(self):
        def prompt_with_args(name: str, age: int = 25, active: bool = True):
            return PromptsContent()

        metadata = FunctionParser(prompt_with_args).function_metadata
        arguments_schema = self.assembler._create_arguments_schema(metadata)

        assert arguments_schema is not None
        assert len(arguments_schema) == 3
        assert arguments_schema[0]["name"] == "name"
        assert arguments_schema[0]["required"] is True
        assert arguments_schema[1]["name"] == "age"
        assert arguments_schema[1]["required"] is False

    def test_build_list_result_schema_and_pagination(self):
        # Add multiple prompts
        for i in range(15):

            def sample_prompt():
                return PromptsContent()

            metadata = FunctionParser(sample_prompt).function_metadata
            registry = PromptRegistry(metadata, {"name": f"prompt{i}"})
            self.assembler.add_registry(registry)

        # Test basic list
        result = self.assembler.build_list_result_schema(page_size=10)
        assert "prompts" in result
        assert len(result["prompts"]) == 10
        assert "nextCursor" in result
        assert result["nextCursor"] is not None

        # Test pagination with cursor
        next_cursor = result["nextCursor"]
        second_page = self.assembler.build_list_result_schema(
            page_size=10, cursor=next_cursor
        )
        assert len(second_page["prompts"]) == 5
        assert second_page.get("nextCursor") is None

    def test_process_result(self):
        def sample_prompt():
            return PromptsContent()

        metadata = FunctionParser(sample_prompt).function_metadata
        registry = PromptRegistry(metadata, {"description": "Test description"})

        # Create PromptsContent with messages
        content = PromptsContent()
        content.add_text("Hello", role=PromptsContent.Roles.USER)
        content.add_text("Hi there!", role=PromptsContent.Roles.ASSISTANT)

        result = self.assembler.process_result(content, registry)

        assert "description" in result
        assert result["description"] == "Test description"
        assert "messages" in result
        assert len(result["messages"]) == 2
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][1]["role"] == "assistant"

    def test_process_result_with_registry_fallback(self):
        def sample_prompt():
            return PromptsContent()

        metadata = FunctionParser(sample_prompt).function_metadata
        registry = PromptRegistry(metadata, {"description": "Registry description"})

        # Content without description
        content = PromptsContent()
        content.add_text("Test message")

        result = self.assembler.process_result(content, registry)

        assert result["description"] == "Registry description"
        assert len(result["messages"]) == 1

    def test_process_result_unsupported_type(self):
        def sample_prompt():
            return PromptsContent()

        metadata = FunctionParser(sample_prompt).function_metadata
        registry = PromptRegistry(metadata)

        with pytest.raises(FeatureSchemaAssembler.UnsupportedResultTypeError):
            self.assembler.process_result("invalid_content", registry)
