"""
JSON-RPC 2.0 serializers for handling request and response data.
"""

import json
from typing import Union, List
from pydantic import ValidationError

from .schema import JsonRpcRequest
from .registry import MCPRegistry
from .managers import RPCRequestManager
from .initializer import MCPInitializer
from . import errors
from .contexts import ResponseContext


class MCPSerializer:
    """Serializer for MCP requests with JSON-RPC 2.0 protocol."""

    def __init__(
        self, initializer: MCPInitializer, registry: MCPRegistry, page_size: int = 10
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

    def process_request(self, request_data: Union[str, dict, list]) -> ResponseContext:
        """Process a JSON-RPC 2.0 request and return a ResponseContext.

        This method handles the complete request-response cycle for MCP servers:
        1. Validates the incoming request data
        2. Deserializes it into JsonRpcRequest object(s)
        3. Routes the request to the appropriate handler
        4. Returns a ResponseContext containing the response and request history

        Args:
            request_data: The JSON-RPC request data. Can be:
                - A JSON string (will be parsed)
                - A dict representing a single request
                - A list of dicts representing a batch request

        Returns:
            ResponseContext: An object containing:
                - response_data: The JSON-RPC response as a dict (or list of dicts for batch)
                - history: List of ResponseEntry objects, each containing:
                    - response: The Pydantic response object
                    - request: The Pydantic request object
                    - data: The response as a dict
                    - is_error: Boolean indicating if this is an error response
                    - is_notification: Boolean indicating if this is a notification

        Example:
            >>> response_ctx = serializer.process_request({
            ...     "jsonrpc": "2.0",
            ...     "id": 1,
            ...     "method": "tools/list",
            ...     "params": {}
            ... })
            >>> print(response_ctx.response_data)
            {'jsonrpc': '2.0', 'id': 1, 'result': {'tools': [...]}}
            >>> print(response_ctx.history[0].is_error)
            False

        Note:
            - Validation and parsing errors are caught and returned as proper error responses
            - Notifications (requests without id) will have response_data set to None
            - Batch requests return a ResponseContext with multiple entries in history
        """
        try:
            request_data = self.validate(request_data)
        except Exception as e:
            error = errors.InvalidRequest(e)
            response_context = ResponseContext()
            response_context.add_context(
                error.get_response(None),
                JsonRpcRequest(jsonrpc="2.0", method="unknown", params=request_data),
            )
            return response_context

        try:
            data = self._deserialize_request(request_data)
        except Exception as e:
            error = errors.ParseError(e)
            response_context = ResponseContext()
            response_context.add_context(
                error.get_response(None),
                JsonRpcRequest(jsonrpc="2.0", method="unknown", params=request_data),
            )
            return response_context

        response_context = self.request_manager.process_request(data)
        return response_context
