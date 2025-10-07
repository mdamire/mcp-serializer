import pytest
import tempfile
from pathlib import Path
from mcp_serializer.features.resource.contents import ResourceContent
from mcp_serializer.features.resource.schema import (
    TextContentSchema,
    BinaryContentSchema,
    AnnotationSchema,
)


class TestResourceContent:
    def setup_method(self):
        self.resource_content = ResourceContent()

    def test_init(self):
        assert self.resource_content.content_list == []

    def test_add_text_content_success(self):
        result = self.resource_content.add_text_content(
            text="Hello world",
            mime_type="text/plain",
            uri="file://test.txt",
            name="test",
        )

        assert isinstance(result, TextContentSchema)
        assert result.text == "Hello world"
        assert result.mimeType == "text/plain"
        assert result.uri == "file://test.txt"
        assert result.name == "test"
        assert len(self.resource_content.content_list) == 1

    def test_add_text_content_validation_error(self):
        with pytest.raises(ValueError, match="Text must be a non-empty string"):
            self.resource_content.add_text_content("", "text/plain")

        with pytest.raises(ValueError, match="Text must be a non-empty string"):
            self.resource_content.add_text_content(None, "text/plain")

    def test_add_binary_content_success(self):
        result = self.resource_content.add_binary_content(
            blob="aGVsbG8gd29ybGQ=",  # base64 for "hello world"
            mime_type="application/octet-stream",
            uri="file://test.bin",
            name="test",
        )

        assert isinstance(result, BinaryContentSchema)
        assert result.blob == "aGVsbG8gd29ybGQ="
        assert result.mimeType == "application/octet-stream"
        assert result.uri == "file://test.bin"
        assert result.name == "test"
        assert len(self.resource_content.content_list) == 1

    def test_add_binary_content_validation_errors(self):
        with pytest.raises(ValueError, match="Blob must be a non-empty string"):
            self.resource_content.add_binary_content("", "application/octet-stream")

        with pytest.raises(ValueError, match="Blob must be valid base64 encoded data"):
            self.resource_content.add_binary_content(
                "invalid_base64!", "application/octet-stream"
            )

    def test_add_file_text_content(self):
        test_content = "This is a test file content"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            result = self.resource_content.add_file(temp_file_path)

            assert isinstance(result, TextContentSchema)
            assert result.text == test_content
            assert result.mimeType == "text/plain"
            assert len(self.resource_content.content_list) == 1
        finally:
            Path(temp_file_path).unlink()

    def test_add_file_process_error(self):
        with pytest.raises(
            ResourceContent.FileProcessError, match="Failed to process file"
        ):
            self.resource_content.add_file("nonexistent_file.unknown")

    def test_multiple_content_items(self):
        # Add text content
        self.resource_content.add_text_content("Text content", "text/plain")

        # Add binary content
        self.resource_content.add_binary_content("aGVsbG8=", "application/octet-stream")

        assert len(self.resource_content.content_list) == 2
        assert isinstance(self.resource_content.content_list[0], TextContentSchema)
        assert isinstance(self.resource_content.content_list[1], BinaryContentSchema)

    def test_content_with_all_optional_fields(self):
        annotation = AnnotationSchema(
            audience="user", priority=0.5, lastModified="2021-01-01T00:00:00Z"
        )
        result = self.resource_content.add_text_content(
            text="Complete content",
            mime_type="text/html",
            uri="https://example.com",
            name="Example",
            title="Example Page",
            annotations=annotation,
        )

        assert result.text == "Complete content"
        assert result.mimeType == "text/html"
        assert result.uri == "https://example.com"
        assert result.name == "Example"
        assert result.title == "Example Page"
        assert result.annotations == annotation
