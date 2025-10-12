import pytest
from mcp_serializer.features.prompt.container import PromptsContainer, PromptRegistry
from mcp_serializer.features.prompt.contents import PromptsContent
from mcp_serializer.features.base.container import FeatureContainer
from mcp_serializer.features.base.parsers import FunctionParser


class TestPromptRegistry:
    def test_init(self):
        def sample_prompt():
            return PromptsContent()

        metadata = FunctionParser(sample_prompt).function_metadata
        registry = PromptRegistry(metadata, {"name": "test_prompt"})

        assert registry.metadata == metadata
        assert registry.extra == {"name": "test_prompt"}

    def test_init_without_extra(self):
        def sample_prompt():
            return PromptsContent()

        metadata = FunctionParser(sample_prompt).function_metadata
        registry = PromptRegistry(metadata)

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
            content = PromptsContent()
            content.add_text("Hello!", role=PromptsContent.Roles.ASSISTANT)
            return content

        # Register the prompt
        metadata = self.container.register(greeting_prompt, name="greeting")
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
            content = PromptsContent()
            if tone == "formal":
                content.add_text(
                    f"Good day, {name}.", role=PromptsContent.Roles.ASSISTANT
                )
            else:
                content.add_text(f"Hey {name}!", role=PromptsContent.Roles.ASSISTANT)
            return content

        self.container.register(personalized_prompt, name="personalized_greeting")

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
            content = PromptsContent()
            content.add_text(f"Message: {required_param}")
            return content

        self.container.register(strict_prompt)

        with pytest.raises(FeatureContainer.RequiredParameterNotFound):
            self.container.call("strict_prompt")  # Missing required parameter

    def test_call_with_wrong_parameter_type(self):
        def typed_prompt(count: int):
            """Prompt expecting integer"""
            content = PromptsContent()
            content.add_text(f"Count: {count}")
            return content

        self.container.register(typed_prompt)

        with pytest.raises(FeatureContainer.ParameterTypeCastingError):
            self.container.call("typed_prompt", count="not_a_number")

    def test_multiple_prompt_registration(self):
        def prompt1():
            """First prompt"""
            return PromptsContent()

        def prompt2():
            """Second prompt"""
            return PromptsContent()

        self.container.register(prompt1, name="first")
        self.container.register(prompt2, name="second")

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
