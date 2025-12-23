from .parsers import FunctionParser
from .definitions import FunctionMetadata
from .schema import cast_python_type


class FeatureContainer:
    class RegistryNotFound(Exception):
        def __init__(self, key: str):
            self.key = key
            super().__init__(f"Key {key} not found")

    class FunctionCallError(Exception):
        def __init__(self, func_name: str, kwargs: dict, error: Exception):
            self.func_name = func_name
            self.kwargs = kwargs
            self.error = error
            super().__init__(f"Failed to call function {func_name}. Error: {error}")

    class ParameterTypeCastingError(Exception):
        def __init__(
            self,
            func_name: str,
            param_name: str,
            param_type: type,
            value: any,
            error: Exception,
        ):
            self.func_name = func_name
            self.param_name = param_name
            self.param_type = param_type
            self.value = value
            self.error = error
            super().__init__(
                f"Failed to cast parameter {param_name} to {param_type} for function {func_name}. Error: {error}"
            )

    class RequiredParameterNotFound(Exception):
        def __init__(self, func_name: str, param_name: str):
            self.func_name = func_name
            self.param_name = param_name
            super().__init__(
                f"Required parameter {param_name} not found for function {func_name}"
            )

    def _get_function_metadata(self, func):
        return FunctionParser(func).function_metadata

    def _get_registry(self, registrations, key):
        if key in registrations:
            return registrations[key]
        raise self.RegistryNotFound(key)

    def _call_function(self, func, kwargs: dict = None):
        try:
            return func(**kwargs) if kwargs else func()
        except Exception as e:
            raise self.FunctionCallError(func.__name__, kwargs, e) from e

    def _validate_parameters(self, func_metadata: FunctionMetadata, kwargs: dict):
        validated_params = {}
        for param_info in func_metadata.arguments:
            param_name = param_info.name
            param_type = param_info.type_hint

            if param_name in kwargs:
                try:
                    # There will be always a type hint for the parameter as the parser sets a default type hint
                    validated_params[param_name] = cast_python_type(
                        kwargs[param_name], param_type
                    )
                except Exception as e:
                    raise self.ParameterTypeCastingError(
                        func_metadata.name,
                        param_name,
                        param_type,
                        kwargs[param_name],
                        e,
                    )
            elif param_info.required:
                raise self.RequiredParameterNotFound(func_metadata.name, param_name)

        return validated_params
