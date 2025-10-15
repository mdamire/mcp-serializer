"""
JSON-RPC 2.0 Pydantic schemas for validation.
"""

from typing import Any, Union, Optional
from pydantic import BaseModel


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request object schema."""

    jsonrpc: str
    method: str
    params: Optional[dict] = {}
    id: Union[str, int, None] = None


class JsonRpcSuccessResponse(BaseModel):
    """JSON-RPC 2.0 success response object schema."""

    jsonrpc: str = "2.0"
    result: Any
    id: Union[str, int, None]


class JsonRpcError(BaseModel):
    """JSON-RPC 2.0 error object schema."""

    code: int
    message: str
    data: Optional[Any] = None


class JsonRpcErrorResponse(BaseModel):
    """JSON-RPC 2.0 error response object schema."""

    jsonrpc: str = "2.0"
    error: JsonRpcError
    id: Union[str, int, None]
