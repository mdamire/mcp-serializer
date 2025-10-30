from .assembler import ResourceSchemaAssembler
from .result import ResourceResult
from ..base.container import FeatureContainer
from ..base.parsers import FunctionParser
from ..base.definitions import FunctionMetadata
from ..base.contents import MimeTypes
from urllib.parse import urlparse


class ResultRegistry:
    def __init__(self, result: ResourceResult, uri: str, extra: dict = None):
        self.result = result
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

    def _add_http_resource(self, uri: str, extra: dict):
        """Determine mime type from URL file extension and add to extra."""
        if not extra.get("mime_type"):
            try:
                url_path = urlparse(uri).path
                extra["mime_type"] = MimeTypes.get_mime_type(url_path)
            except Exception:
                pass

        registry = ResultRegistry(None, uri, extra)
        self.schema_assembler.add_resource_registry(registry)
        return registry

    def add_resource(
        self,
        uri: str,
        result: ResourceResult = None,
        **extra,
    ):
        # For HTTP URIs, content is optional - they appear in list but not callable
        if uri.startswith(("http://", "https://")) and result is None:
            return self._add_http_resource(uri, extra)

        # For non-HTTP URIs or when result is provided, result is required
        if not isinstance(result, ResourceResult):
            raise ValueError("result must be a ResourceResult object")

        registry = ResultRegistry(result, uri, extra)
        self.schema_assembler.add_resource_registry(registry)
        self.registrations[uri] = registry
        return registry

    def register(self, func, uri: str, **extra):
        function_metadata = FunctionParser(func).function_metadata

        # strip trailing slash for resource templates
        if function_metadata.has_arguments:
            uri = uri.rstrip("/")

        # raise error if optional arguments are used with function
        if function_metadata.has_optional_arguments:
            raise ValueError(
                "Optional arguments are not supported for resource registration with function."
            )

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
            result = self._call_function(registry.metadata.function, validated_params)
        else:
            result = registry.result

        processed_result = self.schema_assembler.process_content(result, registry)
        return processed_result
