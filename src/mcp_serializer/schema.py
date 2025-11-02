"""
JSON-RPC 2.0 Pydantic schemas for validation.
"""

from typing import Any, Union, Optional
from pydantic import BaseModel, field_validator


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
    id: Union[int, None]

    @field_validator("id", mode="before")
    @classmethod
    def convert_id_to_int(cls, value):
        """Convert id to int if it's not None."""
        if value is not None:
            return int(value)
        return value


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
