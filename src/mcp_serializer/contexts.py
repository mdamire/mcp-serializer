from typing import Union

from .schema import JsonRpcRequest, JsonRpcErrorResponse, JsonRpcSuccessResponse
from .features.base.assembler import FeatureSchemaAssembler


class ResponseEntry:
    def __init__(
        self,
        response: Union[JsonRpcErrorResponse, JsonRpcSuccessResponse, None],
        request: JsonRpcRequest,
    ):
        self.response = response
        self.request = request

        self.data = self._build_data()

    def _build_data(self) -> dict:
        return (
            FeatureSchemaAssembler()._build_non_none_dict(self.response)
            if self.response
            else None
        )

    @property
    def is_error(self) -> bool:
        return isinstance(self.response, JsonRpcErrorResponse)

    @property
    def is_notification(self) -> bool:
        return self.response is None or self.request.id is None


class ResponseContext:
    def __init__(self):
        self.response_data = None
        self.history = []

    def add_context(
        self,
        response: Union[JsonRpcErrorResponse, JsonRpcSuccessResponse, None],
        request: JsonRpcRequest,
    ):
        item_context = ResponseEntry(response, request)
        self.history.append(item_context)
        data = item_context.data
        if data:
            if isinstance(self.response_data, list):
                self.response_data.append(data)
            elif self.response_data is None:
                self.response_data = data
            else:
                self.response_data = [self.response_data, data]
