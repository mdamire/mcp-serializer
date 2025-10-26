from ..base.container import FeatureContainer
from .assembler import PromptsSchemaAssembler
from ..base.definitions import FunctionMetadata
from .result import PromptsResult


class ResultRegistry:
    def __init__(self, result: PromptsResult, name: str, extra: dict = None):
        self.result = result
        self.name = name
        self.extra = extra or {}


class PromptRegistry:
    def __init__(self, metadata: FunctionMetadata, extra: dict = None):
        self.metadata = metadata
        self.extra = extra or {}


class PromptsContainer(FeatureContainer):
    def __init__(self):
        self.schema_assembler = PromptsSchemaAssembler()
        self.registrations = {}

    def register(self, func, **extra):
        function_metadata = self._get_function_metadata(func)
        registry = PromptRegistry(function_metadata, extra)
        self.schema_assembler.add_registry(registry)
        name = extra.get("name") or function_metadata.name
        self.registrations[name] = registry
        return function_metadata

    def add_text_prompt(
        self,
        name: str,
        text: str,
        role: PromptsResult.Roles = None,
        mime_type: str = None,
        **extra,
    ):
        """Add a text prompt with static content."""
        result = PromptsResult(role=role)
        result.add_text(text=text, mime_type=mime_type)

        registry = ResultRegistry(result, name, extra)
        self.schema_assembler.add_registry(registry)
        self.registrations[name] = registry
        return registry

    def add_file_prompt(
        self,
        name: str,
        file: str,
        role: PromptsResult.Roles = None,
        **extra,
    ):
        """Add a file-based prompt by automatically determining its type."""
        result = PromptsResult(role=role)
        result.add_file_message(file=file)

        registry = ResultRegistry(result, name, extra)
        self.schema_assembler.add_registry(registry)
        self.registrations[name] = registry
        return registry

    def call(self, func_name, **kwargs):
        registry = self._get_registry(self.registrations, func_name)

        if isinstance(registry, PromptRegistry):
            func_metadata = registry.metadata
            validated_params = self._validate_parameters(func_metadata, kwargs)
            result = self._call_function(func_metadata.function, validated_params)
        else:  # ResultRegistry
            result = registry.result

        return self.schema_assembler.process_result(result, registry)
