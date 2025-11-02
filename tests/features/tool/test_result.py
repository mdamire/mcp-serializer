import pytest
from unittest.mock import Mock, patch
from pydantic import BaseModel
from mcp_serializer.features.tool.result import ToolsResult
from mcp_serializer.features.tool.schema import (
    TextContent,
    ImageContent,
    AudioContent,
    ResourceLinkContent,
    EmbeddedResource,
)
from mcp_serializer.features.base.definitions import FileMetadata, ContentTypes
import base64


class SampleModel(BaseModel):
    name: str
    value: int


class TestToolsResult:
    def setup_method(self):
        self.tools_content = ToolsResult()

    def test_init(self):
        assert self.tools_content.content_list == []
        assert self.tools_content.structured_content is None
        assert self.tools_content.is_error is False

    def test_init_with_is_error(self):
        tools_content = ToolsResult(is_error=True)
        assert tools_content.is_error is True

    def test_add_text_success(self):
        result = self.tools_content.add_text_content("Hello world")

        assert isinstance(result, TextContent)
        assert result.text == "Hello world"
        assert len(self.tools_content.content_list) == 1

    def test_add_text_empty_string(self):
        with pytest.raises(ValueError, match="Text must be a non-empty string"):
            self.tools_content.add_text_content("")

    def test_add_text_invalid_type(self):
        with pytest.raises(ValueError, match="Text must be a non-empty string"):
            self.tools_content.add_text_content(123)

    def test_add_image_success(self):
        # Valid base64 data
        valid_base64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA"
        )

        result = self.tools_content.add_image_content(valid_base64, "image/png")

        assert isinstance(result, ImageContent)
        assert result.data == valid_base64
        assert result.mimeType == "image/png"
        assert len(self.tools_content.content_list) == 1

    def test_add_image_with_annotations(self):
        valid_base64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA"
        )
        annotations = {"priority": 1}

        result = self.tools_content.add_image_content(
            valid_base64, "image/png", annotations
        )
        assert result.annotations == annotations

    def test_add_image_empty_data(self):
        with pytest.raises(ValueError, match="Data must be a non-empty string"):
            self.tools_content.add_image_content("", "image/png")

    def test_add_audio_success(self):
        # Valid base64 audio data
        valid_base64 = "UklGRjIAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQ4AAAA="

        result = self.tools_content.add_audio_content(valid_base64, "audio/wav")

        assert isinstance(result, AudioContent)
        assert result.data == valid_base64
        assert result.mimeType == "audio/wav"
        assert len(self.tools_content.content_list) == 1

    def test_add_audio_empty_data(self):
        with pytest.raises(ValueError, match="Data must be a non-empty string"):
            self.tools_content.add_audio_content("", "audio/wav")

    @patch("mcp_serializer.features.tool.result.FileParser")
    def test_add_file_text_success(self, mock_file_parser):
        # Create mock FileMetadata
        mock_metadata = FileMetadata(
            name="file.txt",
            size=100,
            mime_type="text/plain",
            data=b"File content",
            content_type=ContentTypes.TEXT,
        )

        # Mock FileParser to return the metadata
        mock_parser_instance = Mock()
        mock_parser_instance.file_metadata = mock_metadata
        mock_file_parser.return_value = mock_parser_instance

        result = self.tools_content.add_file("/path/to/file.txt", uri="file://test.txt")

        assert isinstance(result, EmbeddedResource)
        assert result.resource.text == "File content"

    @patch("mcp_serializer.features.tool.result.FileParser")
    def test_add_file_image_success(self, mock_file_parser):
        # Valid binary image data
        image_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA"
        )

        # Create mock FileMetadata for image
        mock_metadata = FileMetadata(
            name="image.png",
            size=200,
            mime_type="image/png",
            data=base64.b64encode(image_data).decode("utf-8"),
            content_type=ContentTypes.IMAGE,
        )

        # Mock FileParser to return the metadata
        mock_parser_instance = Mock()
        mock_parser_instance.file_metadata = mock_metadata
        mock_file_parser.return_value = mock_parser_instance

        result = self.tools_content.add_file(
            "/path/to/image.png", uri="file://image.png"
        )

        assert isinstance(result, EmbeddedResource)
        assert result.resource.blob == base64.b64encode(image_data).decode("utf-8")

    @patch("mcp_serializer.features.tool.result.FileParser")
    def test_add_file_all_fail(self, mock_file_parser):
        # Mock FileParser to raise ValueError
        mock_file_parser.side_effect = ValueError(
            "Cannot determine file type from MimeTypes"
        )

        with pytest.raises(ValueError, match="Unable to determine data or mime type"):
            self.tools_content.add_file("/path/to/unknown.file")

    def test_add_resource_link_without_registry(self):
        with pytest.raises(ValueError, match="registry is required for non-HTTP URIs"):
            self.tools_content.add_resource_link("file://test.txt")

    def test_add_resource_link_http_without_registry(self):
        # HTTP URIs should work without registry
        result = self.tools_content.add_resource_link(
            "https://example.com/test.txt",
            name="Test Resource",
            description="A test resource",
            mime_type="text/plain",
        )

        assert isinstance(result, ResourceLinkContent)
        assert result.uri == "https://example.com/test.txt"
        assert result.name == "Test Resource"
        assert result.description == "A test resource"
        assert result.mimeType == "text/plain"

    def test_add_resource_link_with_registry_success(self):
        # Create a mock registry with resource container
        mock_registry = Mock()
        mock_container = Mock()
        mock_resource = Mock()
        mock_resource.uri = "file://test.txt"
        mock_resource.extra = {
            "name": "Test Resource",
            "title": "Test Resource Title",
            "description": "A test resource",
            "mime_type": "text/plain",
        }

        mock_container.schema_assembler.resource_list = [mock_resource]
        mock_container.schema_assembler.resource_template_list = []
        mock_registry.resource_container = mock_container

        result = self.tools_content.add_resource_link(
            "file://test.txt", registry=mock_registry
        )

        assert isinstance(result, ResourceLinkContent)
        assert result.uri == "file://test.txt"
        assert result.name == "Test Resource"
        assert result.title == "Test Resource Title"
        assert result.description == "A test resource"
        assert result.mimeType == "text/plain"

    def test_add_embedded_resource_no_data(self):
        with pytest.raises(
            ValueError, match="Either 'text' or 'blob' must be provided"
        ):
            self.tools_content.add_embedded_resource("https://example.com")

    def test_add_embedded_resource_with_text_data(self):
        result = self.tools_content.add_embedded_resource(
            "https://example.com",
            text="Embedded content",
            mime_type="text/plain",
            name="Test Resource",
        )

        assert isinstance(result, EmbeddedResource)
        assert result.resource.text == "Embedded content"
        assert result.resource.mimeType == "text/plain"

    def test_add_embedded_resource_with_blob_data(self):
        valid_base64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA"
        )

        result = self.tools_content.add_embedded_resource(
            "https://example.com",
            blob=valid_base64,
            mime_type="image/png",
            name="Test Image",
        )

        assert isinstance(result, EmbeddedResource)
        assert result.resource.blob == valid_base64
        assert result.resource.mimeType == "image/png"

    def test_add_embedded_resource_with_title(self):
        result = self.tools_content.add_embedded_resource(
            "https://example.com",
            text="Content with title",
            mime_type="text/plain",
            name="Resource Name",
            title="Resource Title",
        )

        assert isinstance(result, EmbeddedResource)
        assert result.resource.text == "Content with title"
        assert result.resource.name == "Resource Name"
        assert result.resource.title == "Resource Title"

    def test_add_structured_content_pydantic_model(self):
        model = SampleModel(name="test", value=42)
        result = self.tools_content.add_structured_content(model)

        assert self.tools_content.structured_content == {"name": "test", "value": 42}
        assert result == {"name": "test", "value": 42}

    def test_add_structured_content_dictionary(self):
        content_dict = {"key": "value", "number": 123}
        result = self.tools_content.add_structured_content(content_dict)

        assert self.tools_content.structured_content == content_dict
        assert result == content_dict

    def test_add_structured_content_invalid_type(self):
        with pytest.raises(
            ValueError, match="Content must be a valid Pydantic model or dictionary"
        ):
            self.tools_content.add_structured_content("invalid_content")

    def test_add_structured_content_already_exists(self):
        self.tools_content.add_structured_content({"first": "content"})

        with pytest.raises(ValueError, match="Structured content already exists"):
            self.tools_content.add_structured_content({"second": "content"})

    def test_multiple_content_types(self):
        # Add various content types
        self.tools_content.add_text_content("Text content")

        valid_base64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA"
        )
        self.tools_content.add_image_content(valid_base64, "image/png")

        self.tools_content.add_embedded_resource(
            "https://example.com", text="Embedded text", mime_type="text/plain"
        )

        assert len(self.tools_content.content_list) == 3
        assert isinstance(self.tools_content.content_list[0], TextContent)
        assert isinstance(self.tools_content.content_list[1], ImageContent)
        assert isinstance(self.tools_content.content_list[2], EmbeddedResource)
