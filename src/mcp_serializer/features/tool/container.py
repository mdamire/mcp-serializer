from ..base.container import FeatureContainer
from ..base.definitions import FunctionMetadata
from .assembler import ToolsSchemaAssembler


class ToolRegistry:
    def __init__(self, metadata: FunctionMetadata, extra: dict = None):
        self.metadata = metadata
        self.extra = extra or {}


class ToolsContainer(FeatureContainer):
    def __init__(self):
        self.schema_assembler = ToolsSchemaAssembler()
        self.registrations = {}

    def register(self, func, **extra):
        function_metadata = self._get_function_metadata(func)
        registry = ToolRegistry(function_metadata, extra)
        self.schema_assembler.add_tool_registry(registry)
        name = extra.get("name") or function_metadata.name
        self.registrations[name] = registry
        return function_metadata

    def call(self, func_name, **kwargs):
        registry = self._get_registry(self.registrations, func_name)
        validated_params = self._validate_parameters(registry.metadata, kwargs)
        result = self._call_function(registry.metadata.function, validated_params)
        return self.schema_assembler.process_result(result)
