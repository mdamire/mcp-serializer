from typing import List, Optional, Tuple, Any
import base64


class Pagination:
    """Pagination utility for handling cursor-based pagination."""

    class InvalidCursorError(Exception):
        pass

    def __init__(self, size: int):
        if size <= 0:
            raise ValueError("Page size must be greater than 0")
        self.size = size

    def _encode_cursor(self, index: int) -> str:
        """Encode index as base64 cursor."""
        return base64.b64encode(str(index).encode()).decode()

    def _decode_cursor(self, cursor: Optional[str]) -> int:
        """Decode base64 cursor to index."""
        if cursor is None:
            return 0
        try:
            return int(base64.b64decode(cursor.encode()).decode())
        except (ValueError, TypeError) as e:
            raise self.InvalidCursorError(f"Invalid cursor: {cursor}") from e

    def paginate(
        self, items: List[Any], cursor: Optional[str] = None
    ) -> Tuple[List[Any], Optional[str]]:
        if not items:
            return [], None

        start_index = self._decode_cursor(cursor)

        if start_index < 0 or start_index >= len(items):
            return [], None

        # Calculate end index
        end_index = start_index + self.size

        # Get paginated items
        paginated_items = items[start_index:end_index]

        # Determine next cursor
        next_cursor = None
        if end_index < len(items):
            next_cursor = self._encode_cursor(end_index)

        return paginated_items, next_cursor
