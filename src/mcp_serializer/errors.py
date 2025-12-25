from typing import Optional, Any
import traceback
from .schema import JsonRpcError, JsonRpcErrorResponse, JsonRpcRequest


class RPCError:
    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data

    def get_response(self, rpc_request: Optional[JsonRpcRequest]) -> dict:
        id = rpc_request.id if rpc_request is not None else None
        rpc_error = JsonRpcError(code=self.code, message=self.message, data=self.data)
        return JsonRpcErrorResponse(id=id, error=rpc_error)

    def _build_error_data(self, error: Exception) -> dict:
        # Get full traceback including exception type and message
        if error.__traceback__ is not None:
            traceback_lines = traceback.format_exception(
                type(error), error, error.__traceback__
            )
            traceback_str = "".join(traceback_lines)
        else:
            traceback_str = f"{type(error).__name__}: {str(error)}"

        data = {
            "error": str(error),
            "error_type": type(error).__name__,
            "python_exception_traceback": traceback_str,
        }
        return data


class MethodNotFound(RPCError):
    def __init__(self, method: str):
        data = {"method": method}
        super().__init__(-32601, "Method not found", data)
        self.method = method


class InvalidParams(RPCError):
    def __init__(
        self, code=-32602, message="Invalid params", data: Optional[Any] = None
    ):
        super().__init__(code, message, data)


class InternalError(RPCError):
    def __init__(self, error: Exception, message: str = "Internal error"):
        data = self._build_error_data(error)
        super().__init__(-32603, message, data)


class ParseError(RPCError):
    def __init__(self, error: Exception):
        data = self._build_error_data(error)
        super().__init__(-32700, "Parse error", data)


class InvalidRequest(RPCError):
    def __init__(self, error: Exception):
        data = self._build_error_data(error)
        super().__init__(-32600, "Invalid request", data)


class RPCServerError(RPCError):
    def __init__(
        self, code: int, message: str = "Server error", data: Optional[Any] = None
    ):
        super().__init__(code, message, data)
