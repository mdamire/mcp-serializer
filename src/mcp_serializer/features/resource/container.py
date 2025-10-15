from .assembler import ResourceSchemaAssembler
from .contents import ResourceContent
from ..base.container import FeatureContainer
from ..base.parsers import FunctionParser
from ..base.definitions import FunctionMetadata


class ContentRegistry:
    def __init__(self, content: ResourceContent, uri: str, extra: dict = None):
        self.content = content
        self.uri = uri
        self.extra = extra or {}


class FunctionRegistry:
    def __init__(self, metadata: FunctionMetadata, uri: str, extra: dict = None):
        self.metadata = metadata
        self.uri = uri
        self.extra = extra or {}


class ResourceContainer(FeatureContainer):
    def __init__(self):
        self.schema_assembler = ResourceSchemaAssembler()
        self.registrations = {}

    def add_resource(self, uri, content: ResourceContent = None, **extra):
        # get mime type from extra or content
        mime_type = extra.get("mime_type")
        if not mime_type:
            for single_content in content.content_list:
                mime_type = single_content.get("mimeType")
                if mime_type:
                    extra["mime_type"] = mime_type
                    break

        # For HTTP URIs, content is optional - they appear in list but not callable
        if uri.startswith(("http://", "https://")) and content is None:
            registry = ContentRegistry(None, uri, extra)
            self.schema_assembler.add_resource_registry(registry)
            return registry

        # For non-HTTP URIs or when content is provided, content is required
        if not isinstance(content, ResourceContent):
            raise ValueError("Content must be a ResourceContent object")

        registry = ContentRegistry(content, uri, extra)
        self.schema_assembler.add_resource_registry(registry)
        self.registrations[uri] = registry
        return registry

    def register(self, func, uri, **extra):
        function_metadata = FunctionParser(func).function_metadata
        registry = FunctionRegistry(function_metadata, uri, extra)
        self.schema_assembler.add_resource_registry(registry)
        self.registrations[uri] = registry

        return function_metadata

    def _find_exact_match(self, uri: str):
        normalized_uri = uri.rstrip("/")
        for saved_uri in self.registrations.keys():
            if normalized_uri == saved_uri.rstrip("/"):
                return self.registrations[saved_uri]
        return None

    def _find_prefix_match(self, uri: str):
        for saved_uri in sorted(self.registrations.keys()):
            if uri.startswith(saved_uri):
                return self.registrations[saved_uri]
        return None

    def _extract_path_params(self, uri: str, registry):
        remaining_path = uri[len(registry.uri) :].strip("/")
        param_list = remaining_path.split("/") if remaining_path else []

        params = {}
        if isinstance(registry, FunctionRegistry) and param_list:
            for i, param_value in enumerate(param_list):
                if i < len(registry.metadata.arguments):
                    arg_name = registry.metadata.arguments[i].name
                    params[arg_name] = param_value
        return params

    def _get_registry(self, uri: str):
        # Try exact match first
        registry = self._find_exact_match(uri)
        if registry:
            return registry, {}

        # Try prefix match
        registry = self._find_prefix_match(uri)
        if not registry:
            raise self.RegistryNotFound(uri)

        params = self._extract_path_params(uri, registry)

        return registry, params

    def call(self, uri):
        registry, parsed_params = self._get_registry(uri)

        if isinstance(registry, FunctionRegistry):
            validated_params = self._validate_parameters(
                registry.metadata, parsed_params
            )
            result_content = self._call_function(
                registry.metadata.function, validated_params
            )
        else:
            result_content = registry.content

        processed_result = self.schema_assembler.process_content(
            result_content, registry
        )
        return processed_result
