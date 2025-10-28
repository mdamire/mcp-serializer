"""
JSON-RPC 2.0 serializers for handling request and response data.
"""

import json
from typing import Union, List
from pydantic import ValidationError

from .schema import JsonRpcRequest
from .registry import MCPRegistry
from .managers import RPCRequestManager
from .initializer import Initializer
from . import errors


class MCPSerializer:
    """Serializer for MCP requests with JSON-RPC 2.0 protocol."""

    def __init__(
        self, initializer: Initializer, registry: MCPRegistry, page_size: int = 10
    ):
        self.initializer = initializer
        self.registry = registry
        self.request_manager = RPCRequestManager(initializer, registry, page_size)

    def validate(self, request_data: Union[str, dict, list]) -> Union[dict, list]:
        if isinstance(request_data, str):
            try:
                request_data = json.loads(request_data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")

        if isinstance(request_data, list):
            for item in request_data:
                if not isinstance(item, dict):
                    raise ValueError(
                        f"Invalid request data. All items in the list must be dicts. Found {type(item)}"
                    )
        elif not isinstance(request_data, dict):
            raise ValueError(
                f"Invalid request data. Needs to be a dict or list of dicts. Found {type(request_data)}"
            )

        return request_data

    def _deserialize_request(
        self, request_data: Union[dict, list]
    ) -> Union[JsonRpcRequest, List[JsonRpcRequest]]:
        try:
            if isinstance(request_data, list):
                deserialized_data = []
                for item in request_data:
                    deserialized_data.append(JsonRpcRequest(**item))
                return deserialized_data
            else:
                return JsonRpcRequest(**request_data)
        except ValidationError as e:
            raise ValueError(f"Invalid JSON-RPC 2.0 request: {e}")

    def process_request(
        self, request_data: Union[str, dict, list]
    ) -> Union[dict, list, None]:
        try:
            request_data = self.validate(request_data)
        except Exception as e:
            error = errors.InvalidRequest(e)
            response = error.get_response(None)
            return response

        try:
            data = self._deserialize_request(request_data)
        except Exception as e:
            error = errors.ParseError(e)
            response = error.get_response(None)
            return response

        response = self.request_manager.process_request(data)
        return response
