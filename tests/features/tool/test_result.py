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
from mcp_serializer.features.resource.result import ResourceResult
from mcp_serializer.features.resource.container import ResourceContainer


class SampleModel(BaseModel):
    name: str
    value: int


class TestToolsResult:
    def setup_method(self):
        self.tools_content = ToolsResult()

    def test_init(self):
        assert self.tools_content.content_list == []
        assert self.tools_content.resource_container is None
        assert self.tools_content.structured_content is None

    def test_init_with_resource_container(self):
        mock_container = Mock()
        tools_content = ToolsResult(resource_container=mock_container)
        assert tools_content.resource_container == mock_container

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

    def test_add_image_invalid_base64(self):
        with pytest.raises(
            ValueError, match="Data must be valid base64 encoded string"
        ):
            self.tools_content.add_image_content("invalid_base64!", "image/png")

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

    def test_add_audio_invalid_base64(self):
        with pytest.raises(
            ValueError, match="Data must be valid base64 encoded string"
        ):
            self.tools_content.add_audio_content("invalid_base64!", "audio/wav")

    @patch("mcp_serializer.features.tool.result.TextContentSanitizer")
    def test_add_file_text_success(self, mock_sanitizer):
        mock_instance = Mock()
        mock_instance.text = "File content"
        mock_instance.mime_type = "text/plain"
        mock_sanitizer.return_value = mock_instance

        result = self.tools_content.add_file("/path/to/file.txt")

        assert isinstance(result, TextContent)
        assert result.text == "File content"

    @patch("mcp_serializer.features.tool.result.TextContentSanitizer")
    @patch("mcp_serializer.features.tool.result.ImageContentSanitizer")
    def test_add_file_image_success(self, mock_image_sanitizer, mock_text_sanitizer):
        # Text sanitizer fails
        mock_text_sanitizer.side_effect = Exception("Not text")

        # Image sanitizer succeeds
        valid_base64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA"
        )
        mock_image_instance = Mock()
        mock_image_instance.data = valid_base64
        mock_image_instance.mime_type = "image/png"
        mock_image_sanitizer.return_value = mock_image_instance

        result = self.tools_content.add_file("/path/to/image.png")

        assert isinstance(result, ImageContent)
        assert result.data == valid_base64

    @patch("mcp_serializer.features.tool.result.TextContentSanitizer")
    @patch("mcp_serializer.features.tool.result.ImageContentSanitizer")
    @patch("mcp_serializer.features.tool.result.AudioContentSanitizer")
    def test_add_file_all_fail(self, mock_audio, mock_image, mock_text):
        # All sanitizers fail
        mock_text.side_effect = Exception("Text error")
        mock_image.side_effect = Exception("Image error")
        mock_audio.side_effect = Exception("Audio error")

        with pytest.raises(ValueError, match="Unable to determine data or mime type"):
            self.tools_content.add_file("/path/to/unknown.file")

    def test_add_resource_link_without_container(self):
        with pytest.raises(ToolsResult.ResourceContainerRequiredError):
            self.tools_content.add_resource_link("/a/b/c", mime_type="text/html")

    def test_add_resource_link_with_container_success(self):
        # Create actual ResourceContainer and add a resource with content
        resource_container = ResourceContainer()
        resource_content = ResourceResult()
        resource_content.add_text_content("Sample text content", "text/plain")

        resource_container.add_resource(
            "file://test.txt",
            resource_content,
            name="Test Resource",
            description="A test resource",
            mimeType="text/plain",
        )

        # Create ToolsResult with the actual resource container
        tools_content = ToolsResult(resource_container=resource_container)
        result = tools_content.add_resource_link("file://test.txt")

        assert isinstance(result, ResourceLinkContent)
        assert result.uri == "file://test.txt"
        assert result.name == "Test Resource"
        assert result.description == "A test resource"
        assert result.mimeType == "text/plain"

    def test_add_embedded_resource_no_container_no_data(self):
        with pytest.raises(ToolsResult.ResourceContainerRequiredError):
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

    def test_add_embedded_resource_with_container(self):
        mock_container = Mock()
        mock_container.call.return_value = {
            "contents": [
                {
                    "text": "Resource content",
                    "mimeType": "text/plain",
                    "name": "Test Resource",
                }
            ]
        }

        tools_content = ToolsResult(resource_container=mock_container)
        result = tools_content.add_embedded_resource("file://test.txt")

        assert isinstance(result, EmbeddedResource)
        assert result.resource.text == "Resource content"
        assert result.resource.name == "Test Resource"

    def test_add_embedded_resource_container_fails_no_fallback(self):
        mock_container = Mock()
        mock_container.call.side_effect = Exception("Resource not found")

        tools_content = ToolsResult(resource_container=mock_container)

        with pytest.raises(ToolsResult.ResourceNotFoundError):
            tools_content.add_embedded_resource("file://nonexistent.txt")

    def test_add_embedded_resource_no_mime_type(self):
        with pytest.raises(ValueError):
            self.tools_content.add_embedded_resource(
                "https://example.com", text="Content without mime type"
            )

    def test_add_embedded_resource_no_content(self):
        with pytest.raises(ToolsResult.ResourceContainerRequiredError):
            self.tools_content.add_embedded_resource(
                "https://example.com", mime_type="text/plain"
            )

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
