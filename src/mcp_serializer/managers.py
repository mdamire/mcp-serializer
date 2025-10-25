from typing import Union, List
from copy import deepcopy

from pydantic import BaseModel

from .registry import MCPRegistry
from .schema import (
    JsonRpcRequest,
    JsonRpcErrorResponse,
    JsonRpcSuccessResponse,
)
from .logging import get_logger
from .initializer import Initializer
from . import errors
from .features.base.container import FeatureContainer
from .features.base.assembler import FeatureSchemaAssembler


class RPCRequestManager:
    class InvalidMethod(Exception):
        def __init__(self, method_type: str):
            self.method_type = method_type
            super().__init__(f"Invalid method type: {method_type}")

    class FeatureNotInitialized(Exception):
        def __init__(self, feature_name: str):
            self.feature_name = feature_name
            super().__init__(f"Feature {feature_name} is not initialized")

    class ProcessingError(Exception):
        def __init__(self, feature_name: str, rpc_error: errors.RPCError):
            self.feature_name = feature_name
            self.rpc_error = rpc_error
            super().__init__(f"Error processing {feature_name} request")

    class MethodPrefix:
        initialize = "initialize"
        tools = "tools"
        resources = "resources"
        prompts = "prompts"

    def __init__(self, initializer: Initializer, registry: MCPRegistry, page_size):
        self.registry = registry
        self.initializer = initializer
        self.page_size = page_size

    def _process_initialize_request(self, rpc_params, **kwargs):
        result = self.initializer.build_result(rpc_params)
        if (
            self.MethodPrefix.tools in result["capabilities"]
            and self.registry.tools_container is None
        ):
            del result["capabilities"][self.MethodPrefix.tools]
        if (
            self.MethodPrefix.resources in result["capabilities"]
            and self.registry.resource_container is None
        ):
            del result["capabilities"][self.MethodPrefix.resources]
        if (
            self.MethodPrefix.prompts in result["capabilities"]
            and self.registry.prompt_container is None
        ):
            del result["capabilities"][self.MethodPrefix.prompts]
        return result

    def _process_tools_request(self, rpc_params, method_type, cursor):
        if self.registry.tools_container is None:
            raise self.FeatureNotInitialized("tools")
        if method_type == "list":
            return (
                self.registry.tools_container.schema_assembler.build_list_result_schema(
                    page_size=self.page_size, cursor=cursor
                )
            )
        elif method_type == "call":
            name = rpc_params["name"]
            kwargs = rpc_params.get("arguments", {})
            try:
                return self.registry.tools_container.call(name, **kwargs)
            except Exception as e:
                data = {"tool_name": name, "arguments": kwargs, "error": str(e)}

                if isinstance(e, FeatureContainer.FunctionCallError):
                    error = errors.RPCServerError(-32001, "Tools call error", data)
                elif isinstance(e, FeatureContainer.RegistryNotFound):
                    error = errors.RPCServerError(-32002, "Could not find tool", data)
                elif isinstance(e, FeatureContainer.ParameterTypeCastingError):
                    data["invalid_parameter_name"] = e.param_name
                    data["invalid_parameter_value"] = e.value
                    data["expected_parameter_type"] = e.param_type
                    error = errors.InvalidParams(
                        message="Invalid parameters for tools", data=data
                    )
                elif isinstance(e, FeatureContainer.RequiredParameterNotFound):
                    data["missing_parameter"] = e.param_name
                    error = errors.InvalidParams(
                        message="Required parameter not found for tools", data=data
                    )
                else:
                    raise e
                raise self.ProcessingError("tools", error) from e
        else:
            raise self.InvalidMethod(method_type)

    def _process_resources_request(self, rpc_params, method_type, cursor):
        if self.registry.resource_container is None:
            raise self.FeatureNotInitialized("resources")
        if method_type == "list":
            return self.registry.resource_container.schema_assembler.build_list_result_schema(
                page_size=self.page_size, cursor=cursor
            )
        elif method_type == "templates/list":
            return self.registry.resource_container.schema_assembler.build_template_list_result_schema(
                page_size=self.page_size, cursor=cursor
            )
        elif method_type == "read":
            uri = rpc_params["uri"]
            try:
                return self.registry.resource_container.call(uri)
            except Exception as e:
                data = {"uri": uri, "error": str(e)}
                if isinstance(e, FeatureContainer.FunctionCallError):
                    error = errors.RPCServerError(-32003, "Resources fetch error", data)
                elif isinstance(e, FeatureContainer.RegistryNotFound):
                    error = errors.RPCServerError(
                        -32004, "Could not find resource", data
                    )
                elif isinstance(e, FeatureContainer.RequiredParameterNotFound):
                    data["missing_parameter"] = e.param_name
                    error = errors.RPCServerError(
                        -32005, "Parameter is required in resource template", data
                    )
                elif isinstance(e, FeatureSchemaAssembler.UnsupportedResultTypeError):
                    error = errors.InternalError(
                        e, "Feature returned unsupported type. Check return values."
                    )
                else:
                    raise e
                raise self.ProcessingError("resources", error) from e
        else:
            raise self.InvalidMethod(method_type)

    def _process_prompts_request(self, rpc_params, method_type, cursor):
        if self.registry.prompt_container is None:
            raise self.FeatureNotInitialized("prompts")
        if method_type == "list":
            return self.registry.prompt_container.schema_assembler.build_list_result_schema(
                page_size=self.page_size, cursor=cursor
            )
        elif method_type == "get":
            name = rpc_params["name"]
            kwargs = rpc_params.get("arguments", {})
            try:
                return self.registry.prompt_container.call(name, **kwargs)
            except Exception as e:
                data = {"prompt_name": name, "arguments": kwargs, "error": str(e)}
                if isinstance(e, FeatureContainer.FunctionCallError):
                    error = errors.RPCServerError(-32006, "Prompts call error", data)
                elif isinstance(e, FeatureContainer.RegistryNotFound):
                    error = errors.RPCServerError(-32007, "Could not find prompt", data)
                elif isinstance(e, FeatureContainer.ParameterTypeCastingError):
                    data["invalid_parameter_name"] = e.param_name
                    data["invalid_parameter_value"] = e.value
                    data["expected_parameter_type"] = e.param_type
                    error = errors.InvalidParams(
                        message="Invalid parameters for prompts", data=data
                    )
                elif isinstance(e, FeatureContainer.RequiredParameterNotFound):
                    data["missing_parameter"] = e.param_name
                    error = errors.InvalidParams(
                        message="Required parameter not found for prompts", data=data
                    )
                else:
                    raise e
                raise self.ProcessingError("prompts", error) from e
        else:
            raise self.InvalidMethod(method_type)

    def _get_processor_mapping(self):
        return {
            self.MethodPrefix.initialize: self._process_initialize_request,
            self.MethodPrefix.tools: self._process_tools_request,
            self.MethodPrefix.resources: self._process_resources_request,
            self.MethodPrefix.prompts: self._process_prompts_request,
        }

    def _pop_cursor_param(self, rpc_params):
        if "cursor" in rpc_params:
            cursor = rpc_params.pop("cursor")
            return cursor
        return None

    def _process_result(self, result):
        if isinstance(result, BaseModel):
            return result.model_dump()
        if type(result) not in [dict, type(None)]:
            raise ValueError(f"Invalid result type: {type(result)}")
        return result

    def _process_single_result(self, rpc_request: JsonRpcRequest) -> Union[dict, None]:
        """It should return a rpc result object."""
        processor_mapping = self._get_processor_mapping()

        # log if notification
        if rpc_request.id is None:
            get_logger().info(f"Notification: {rpc_request.method}")
            return None

        # prepare processor
        try:
            method_name, method_type = rpc_request.method.split("/", 1)
        except Exception:
            method_name, method_type = rpc_request.method, None

        if method_name not in processor_mapping:
            raise self.InvalidMethod(method_name)

        processor = processor_mapping[method_name]
        params = deepcopy(rpc_request.params)
        cursor = self._pop_cursor_param(params)

        # process request
        result = processor(rpc_params=params, method_type=method_type, cursor=cursor)

        # process result
        result = self._process_result(result)

        return result

    def _build_success_response(
        self, rpc_request: JsonRpcRequest, result: dict
    ) -> JsonRpcSuccessResponse:
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        response = JsonRpcSuccessResponse(id=rpc_request.id, result=result).model_dump()
        return response

    def _process_single_request(self, rpc_request: JsonRpcRequest) -> Union[dict, None]:
        try:
            result = self._process_single_result(rpc_request)
            response = (
                self._build_success_response(rpc_request, result)
                if result is not None
                else None
            )
        except Exception as e:
            get_logger().exception(e)
            if isinstance(e, self.ProcessingError):
                error = e.rpc_error
            elif isinstance(e, self.InvalidMethod):
                error = errors.MethodNotFound(rpc_request.method)
            elif isinstance(e, self.FeatureNotInitialized):
                error = errors.MethodNotFound(rpc_request.method)
            else:
                error = errors.InternalError(e)
            response = error.get_response(rpc_request)
        return response

    def process_request(
        self, rpc_request: Union[JsonRpcRequest, List[JsonRpcRequest]]
    ) -> Union[JsonRpcSuccessResponse, JsonRpcErrorResponse]:
        if isinstance(rpc_request, list):
            response_list = []
            for request in rpc_request:
                response = self._process_single_request(request)
                if response is not None:
                    response_list.append(response)

            return response_list if response_list else None

        response = self._process_single_request(rpc_request)
        return response
