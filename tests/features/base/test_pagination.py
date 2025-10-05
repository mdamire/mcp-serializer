import pytest
from mcp_serializer.features.base.pagination import Pagination


class TestPagination:
    def test_initialization_valid_size(self):
        """Test pagination initialization with valid size."""
        pagination = Pagination(10)
        assert pagination.size == 10

    def test_initialization_invalid_size(self):
        """Test pagination initialization with invalid sizes."""
        with pytest.raises(ValueError, match="Page size must be greater than 0"):
            Pagination(0)

        with pytest.raises(ValueError, match="Page size must be greater than 0"):
            Pagination(-1)

    def test_paginate_empty_list(self):
        """Test pagination with empty list."""
        pagination = Pagination(5)
        items, next_cursor = pagination.paginate([])
        assert items == []
        assert next_cursor is None

    def test_paginate_first_page(self):
        """Test pagination for first page."""
        pagination = Pagination(3)
        test_items = [1, 2, 3, 4, 5, 6, 7]

        items, next_cursor = pagination.paginate(test_items)

        assert items == [1, 2, 3]
        assert pagination._decode_cursor(next_cursor) == 3

    def test_with_invalid_cursor(self):
        pagination = Pagination(3)
        test_items = [1, 2, 3, 4, 5, 6, 7]

        # Test with invalid cursor
        with pytest.raises(Pagination.InvalidCursorError, match="Invalid cursor"):
            pagination.paginate(test_items, "invalid_cursor")

        with pytest.raises(Pagination.InvalidCursorError, match="Invalid cursor"):
            pagination.paginate(test_items, "not_base64!")

    def test_pagination_with_cursor(self):
        """Test pagination with cursor using invalid cursor to test decode functionality."""
        pagination = Pagination(3)
        test_items = [1, 2, 3, 4, 5, 6, 7]

        # get next cursor
        items, next_cursor = pagination.paginate(test_items)
        assert pagination._decode_cursor(next_cursor) == 3

        # Test with valid cursor
        items, next_cursor = pagination.paginate(test_items, next_cursor)

        assert items == [4, 5, 6]
        assert pagination._decode_cursor(next_cursor) == 6

        # Test last page
        items, next_cursor = pagination.paginate(test_items, next_cursor)
        assert items == [7]
        assert next_cursor is None

    def test_paginate_exact_page_boundary(self):
        """Test pagination when items exactly fill pages."""
        pagination = Pagination(3)
        test_items = [1, 2, 3, 4, 5, 6]
        cursor = pagination._encode_cursor(3)

        items, next_cursor = pagination.paginate(test_items, cursor)

        assert items == [4, 5, 6]
        assert next_cursor is None
