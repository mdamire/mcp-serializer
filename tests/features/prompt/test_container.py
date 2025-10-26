import pytest
from unittest.mock import Mock, patch
from mcp_serializer.features.prompt.container import (
    PromptsContainer,
    PromptRegistry,
    ResultRegistry,
)
from mcp_serializer.features.prompt.result import PromptsResult
from mcp_serializer.features.base.container import FeatureContainer
from mcp_serializer.features.base.parsers import FunctionParser


class TestPromptRegistry:
    def test_init(self):
        def sample_prompt():
            return PromptsResult()

        metadata = FunctionParser(sample_prompt).function_metadata
        registry = PromptRegistry(metadata, {"name": "test_prompt"})

        assert registry.metadata == metadata
        assert registry.extra == {"name": "test_prompt"}

    def test_init_without_extra(self):
        def sample_prompt():
            return PromptsResult()

        metadata = FunctionParser(sample_prompt).function_metadata
        registry = PromptRegistry(metadata)

        assert registry.extra == {}


class TestResultRegistry:
    def test_init(self):
        result = PromptsResult()
        result.add_text("Sample text")

        registry = ResultRegistry(result, "test_prompt", {"title": "Test Prompt"})

        assert registry.result == result
        assert registry.name == "test_prompt"
        assert registry.extra == {"title": "Test Prompt"}

    def test_init_without_extra(self):
        result = PromptsResult()
        registry = ResultRegistry(result, "test_prompt")

        assert registry.extra == {}


class TestPromptsContainer:
    def setup_method(self):
        self.container = PromptsContainer()

    def test_init(self):
        assert self.container.registrations == {}
        assert hasattr(self.container, "schema_assembler")

    def test_register_and_call_basic(self):
        def greeting_prompt():
            """Generate a greeting"""
            content = PromptsResult()
            content.add_text("Hello!", role=PromptsResult.Roles.ASSISTANT)
            return content

        # Register the prompt
        metadata = self.container.register(greeting_prompt)
        assert metadata.name == "greeting_prompt"
        assert "greeting_prompt" in self.container.registrations

        # Call the prompt
        result = self.container.call("greeting_prompt")
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "assistant"

    def test_register_and_call_with_parameters(self):
        def personalized_prompt(name: str, tone: str = "friendly"):
            """Generate personalized greeting"""
            content = PromptsResult()
            if tone == "formal":
                content.add_text(
                    f"Good day, {name}.", role=PromptsResult.Roles.ASSISTANT
                )
            else:
                content.add_text(f"Hey {name}!", role=PromptsResult.Roles.ASSISTANT)
            return content

        self.container.register(personalized_prompt)

        # Test with default parameter
        result1 = self.container.call("personalized_prompt", name="Alice")
        assert "Hey Alice!" in str(result1["messages"][0])

        # Test with explicit parameter
        result2 = self.container.call("personalized_prompt", name="Bob", tone="formal")
        assert "Good day, Bob." in str(result2["messages"][0])

    def test_call_nonexistent_prompt(self):
        with pytest.raises(FeatureContainer.RegistryNotFound):
            self.container.call("nonexistent_prompt")

    def test_call_with_invalid_parameters(self):
        def strict_prompt(required_param: str):
            """Prompt with required parameter"""
            content = PromptsResult()
            content.add_text(f"Message: {required_param}")
            return content

        self.container.register(strict_prompt)

        with pytest.raises(FeatureContainer.RequiredParameterNotFound):
            self.container.call("strict_prompt")  # Missing required parameter

    def test_call_with_wrong_parameter_type(self):
        def typed_prompt(count: int):
            """Prompt expecting integer"""
            content = PromptsResult()
            content.add_text(f"Count: {count}")
            return content

        self.container.register(typed_prompt)

        with pytest.raises(FeatureContainer.ParameterTypeCastingError):
            self.container.call("typed_prompt", count="not_a_number")

    def test_multiple_prompt_registration(self):
        def prompt1():
            """First prompt"""
            return PromptsResult()

        def prompt2():
            """Second prompt"""
            return PromptsResult()

        self.container.register(prompt1)
        self.container.register(prompt2)

        assert len(self.container.registrations) == 2
        assert "prompt1" in self.container.registrations
        assert "prompt2" in self.container.registrations

        # Test list schema generation
        result = self.container.schema_assembler.build_list_result_schema()
        assert len(result["prompts"]) == 2

    def test_prompt_execution_error(self):
        def error_prompt():
            """Prompt that raises an error"""
            raise RuntimeError("Prompt error")

        self.container.register(error_prompt)

        with pytest.raises(FeatureContainer.FunctionCallError):
            self.container.call("error_prompt")

    def test_add_text_prompt(self):
        """Test adding text prompts with various parameters."""
        # Basic text prompt
        registry = self.container.add_text_prompt(
            name="greeting",
            text="Hello, how can I help you?",
            role=PromptsResult.Roles.ASSISTANT,
            mime_type="text/markdown",
            title="Help Prompt",
            description="A prompt to ask how to help the user",
        )

        assert isinstance(registry, ResultRegistry)
        assert registry.name == "greeting"
        assert "greeting" in self.container.registrations

        # Call the prompt and verify all parameters
        result = self.container.call("greeting")
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "assistant"
        assert result["messages"][0]["content"]["text"] == "Hello, how can I help you?"
        assert result["messages"][0]["content"]["mimeType"] == "text/markdown"
        assert result["description"] == "A prompt to ask how to help the user"

        # Check it appears in the list schema
        list_result = self.container.schema_assembler.build_list_result_schema()
        prompt_def = next(p for p in list_result["prompts"] if p["name"] == "greeting")
        assert prompt_def["title"] == "Help Prompt"
        assert prompt_def["description"] == "A prompt to ask how to help the user"

    @patch("mcp_serializer.features.prompt.result.FileParser")
    def test_add_file_prompt(self, mock_file_parser):
        """Test adding file prompts with text and image content."""
        from mcp_serializer.features.base.definitions import FileMetadata, ContentTypes
        import base64

        # Test text file with all parameters
        mock_text_metadata = FileMetadata(
            name="doc.txt",
            size=150,
            mime_type="text/plain",
            data=b"Documentation content",
            content_type=ContentTypes.TEXT,
            uri="file://doc.txt",
        )

        mock_parser_instance = Mock()
        mock_parser_instance.file_metadata = mock_text_metadata
        mock_file_parser.return_value = mock_parser_instance

        registry = self.container.add_file_prompt(
            name="documentation",
            file="/path/to/doc.txt",
            role=PromptsResult.Roles.ASSISTANT,
            title="Documentation Prompt",
            description="System documentation",
        )

        assert isinstance(registry, ResultRegistry)
        assert "documentation" in self.container.registrations

        result = self.container.call("documentation")
        assert result["messages"][0]["role"] == "assistant"
        assert result["messages"][0]["content"]["text"] == "Documentation content"
        assert result["messages"][0]["content"]["mimeType"] == "text/plain"
        assert result["description"] == "System documentation"

        # Test image file
        mock_image_metadata = FileMetadata(
            name="image.png",
            size=200,
            mime_type="image/png",
            data=b"fake_image_data",
            content_type=ContentTypes.IMAGE,
            uri="file://image.png",
        )

        mock_parser_instance.file_metadata = mock_image_metadata
        self.container.add_file_prompt(name="image_prompt", file="/path/to/image.png")

        result = self.container.call("image_prompt")
        assert result["messages"][0]["content"]["type"] == "image"
        assert result["messages"][0]["content"]["mimeType"] == "image/png"
        assert result["messages"][0]["content"]["data"] == base64.b64encode(
            b"fake_image_data"
        ).decode("utf-8")

    def test_mixed_prompt_types(self):
        """Test mixing function-based and static prompts."""

        def dynamic_prompt(name: str):
            """Dynamic greeting"""
            content = PromptsResult()
            content.add_text(f"Hello {name}!", role=PromptsResult.Roles.ASSISTANT)
            return content

        # Register function-based prompt
        self.container.register(dynamic_prompt)

        # Add static text prompt
        self.container.add_text_prompt(
            name="static_greeting", text="Welcome to our service!"
        )

        assert len(self.container.registrations) == 2

        # Both should be callable
        result1 = self.container.call("dynamic_prompt", name="Alice")
        assert "Hello Alice!" in str(result1["messages"][0])

        result2 = self.container.call("static_greeting")
        assert "Welcome to our service!" in str(result2["messages"][0])

        # Both should appear in list schema
        list_result = self.container.schema_assembler.build_list_result_schema()
        assert len(list_result["prompts"]) == 2
