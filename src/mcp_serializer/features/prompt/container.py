from ..base.container import FeatureContainer
from .assembler import PromptsSchemaAssembler
from ..base.definitions import FunctionMetadata


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
        registry_data = PromptRegistry(function_metadata, extra)
        self.schema_assembler.add_registry(registry_data)
        self.registrations[func.__name__] = registry_data
        return function_metadata

    def call(self, func_name, **kwargs):
        registry = self._get_registry(self.registrations, func_name)
        func_metadata = registry.metadata
        validated_params = self._validate_parameters(func_metadata, kwargs)
        result = self._call_function(func_metadata.function, validated_params)
        return self.schema_assembler.process_result(result, registry)
