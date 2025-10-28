import base64
import pytest
from unittest.mock import Mock, patch
from pydantic import BaseModel
from mcp_serializer.features.prompt.result import PromptsResult
from mcp_serializer.features.prompt.schema import (
    TextContent,
    ImageContent,
    AudioContent,
    EmbeddedResource,
)
from mcp_serializer.features.resource.container import ResourceContainer
from mcp_serializer.features.resource.result import ResourceResult
from mcp_serializer.features.base.definitions import FileMetadata, ContentTypes


class TestPromptsResult:
    def setup_method(self):
        self.prompts_content = PromptsResult()

    def test_init_and_roles_enum(self):
        # Test default initialization
        assert self.prompts_content.messages == []
        assert self.prompts_content.default_role == PromptsResult.Roles.USER.value
        assert self.prompts_content.resource_container is None

        # Test Roles enum
        assert PromptsResult.Roles.USER.value == "user"
        assert PromptsResult.Roles.ASSISTANT.value == "assistant"
        assert PromptsResult.Roles.has_value("user") is True
        assert PromptsResult.Roles.has_value("invalid") is False

        # Test with custom role
        custom_prompts = PromptsResult(role=PromptsResult.Roles.USER)
        assert custom_prompts.default_role == PromptsResult.Roles.USER.value

    def test_add_text_with_roles(self):
        # Test with explicit role
        result1 = self.prompts_content.add_text("Hello", role=PromptsResult.Roles.USER)
        assert isinstance(result1, TextContent)
        assert result1.text == "Hello"
        assert len(self.prompts_content.messages) == 1
        assert self.prompts_content.messages[0]["role"] == "user"

        # Test with default role
        result2 = self.prompts_content.add_text("Hi there!")
        assert len(self.prompts_content.messages) == 2
        assert self.prompts_content.messages[1]["role"] == "user"

    def test_add_text_validation(self):
        with pytest.raises(ValueError, match="Text must be a non-empty string"):
            self.prompts_content.add_text("")

        with pytest.raises(ValueError, match="Text must be a non-empty string"):
            self.prompts_content.add_text(123)

    def test_add_text_with_mime_type(self):
        # Test with mime type
        result = self.prompts_content.add_text(
            "Sample text", role=PromptsResult.Roles.USER, mime_type="text/plain"
        )
        assert isinstance(result, TextContent)
        assert result.text == "Sample text"
        assert result.mimeType == "text/plain"
        assert self.prompts_content.messages[0]["content"]["mimeType"] == "text/plain"

        # Test without mime type (should be None)
        result2 = self.prompts_content.add_text("Another text")
        assert result2.mimeType is None

    def test_add_image_and_audio(self):
        valid_base64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA"
        )

        # Test image
        image_result = self.prompts_content.add_image(
            valid_base64, "image/png", role=PromptsResult.Roles.USER
        )
        assert isinstance(image_result, ImageContent)
        assert image_result.data == valid_base64
        assert image_result.mimeType == "image/png"
        assert self.prompts_content.messages[0]["role"] == "user"

        # Test audio
        audio_base64 = "UklGRjIAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQ4AAAA="
        audio_result = self.prompts_content.add_audio(
            audio_base64, "audio/wav", role=PromptsResult.Roles.ASSISTANT
        )
        assert isinstance(audio_result, AudioContent)
        assert audio_result.data == audio_base64
        assert self.prompts_content.messages[1]["role"] == "assistant"

    def test_add_media_validation(self):
        # Test image validation
        with pytest.raises(ValueError, match="Data must be a non-empty string"):
            self.prompts_content.add_image("", "image/png")

        with pytest.raises(ValueError, match="MIME type is required for image content"):
            self.prompts_content.add_image("valid_data", "")

        # Test audio validation
        with pytest.raises(ValueError, match="Data must be a non-empty string"):
            self.prompts_content.add_audio("", "audio/wav")

        with pytest.raises(ValueError, match="MIME type is required for audio content"):
            self.prompts_content.add_audio("valid_data", "")

    @patch("mcp_serializer.features.prompt.result.FileParser")
    def test_add_file_resource_text_success(self, mock_file_parser):
        # Create mock FileMetadata
        mock_metadata = FileMetadata(
            name="file.txt",
            size=100,
            mime_type="text/plain",
            data="File content",
            content_type=ContentTypes.TEXT,
            uri="file://file.txt",
        )

        # Mock FileParser to return the metadata
        mock_parser_instance = Mock()
        mock_parser_instance.file_metadata = mock_metadata
        mock_file_parser.return_value = mock_parser_instance

        result = self.prompts_content.add_file_resource(
            "/path/to/file.txt", role=PromptsResult.Roles.USER
        )

        assert isinstance(result, EmbeddedResource)
        assert result.resource.text == "File content"
        assert self.prompts_content.messages[0]["role"] == "user"

    @patch("mcp_serializer.features.prompt.result.FileParser")
    def test_add_file_resource_all_fail(self, mock_file_parser):
        # Mock FileParser to raise ValueError
        mock_file_parser.side_effect = ValueError(
            "Cannot determine file type from MimeTypes"
        )

        with pytest.raises(ValueError, match="Unable to process file"):
            self.prompts_content.add_file_resource("/path/to/unknown.file")

    @patch("mcp_serializer.features.prompt.result.FileParser")
    def test_add_file_message_text(self, mock_file_parser):
        # Create mock FileMetadata for text file
        mock_metadata = FileMetadata(
            name="file.txt",
            size=100,
            mime_type="text/plain",
            data="Text file content",
            content_type=ContentTypes.TEXT,
            uri="file://file.txt",
        )

        # Mock FileParser to return the metadata
        mock_parser_instance = Mock()
        mock_parser_instance.file_metadata = mock_metadata
        mock_file_parser.return_value = mock_parser_instance

        result = self.prompts_content.add_file_message(
            "/path/to/file.txt", role=PromptsResult.Roles.USER
        )

        assert isinstance(result, TextContent)
        assert result.text == "Text file content"
        assert result.mimeType == "text/plain"
        assert self.prompts_content.messages[0]["role"] == "user"
        assert self.prompts_content.messages[0]["content"]["type"] == "text"
        assert self.prompts_content.messages[0]["content"]["mimeType"] == "text/plain"

    @patch("mcp_serializer.features.prompt.result.FileParser")
    def test_add_file_message_image(self, mock_file_parser):
        # Create mock FileMetadata for image file
        mock_metadata = FileMetadata(
            name="image.png",
            size=200,
            mime_type="image/png",
            data=base64.b64encode(b"fake_image_data").decode("utf-8"),
            content_type=ContentTypes.IMAGE,
            uri="file://image.png",
        )

        # Mock FileParser to return the metadata
        mock_parser_instance = Mock()
        mock_parser_instance.file_metadata = mock_metadata
        mock_file_parser.return_value = mock_parser_instance

        result = self.prompts_content.add_file_message(
            "/path/to/image.png", role=PromptsResult.Roles.USER
        )

        assert isinstance(result, ImageContent)
        assert result.mimeType == "image/png"

        assert result.data == base64.b64encode(b"fake_image_data").decode("utf-8")
        assert self.prompts_content.messages[0]["role"] == "user"
        assert self.prompts_content.messages[0]["content"]["type"] == "image"

    @patch("mcp_serializer.features.prompt.result.FileParser")
    def test_add_file_message_audio(self, mock_file_parser):
        # Create mock FileMetadata for audio file
        data = base64.b64encode(b"fake_audio_data").decode("utf-8")
        mock_metadata = FileMetadata(
            name="audio.wav",
            size=300,
            mime_type="audio/wav",
            data=data,
            content_type=ContentTypes.AUDIO,
            uri="file://audio.wav",
        )

        # Mock FileParser to return the metadata
        mock_parser_instance = Mock()
        mock_parser_instance.file_metadata = mock_metadata
        mock_file_parser.return_value = mock_parser_instance

        result = self.prompts_content.add_file_message(
            "/path/to/audio.wav", role=PromptsResult.Roles.ASSISTANT
        )

        assert isinstance(result, AudioContent)
        assert result.mimeType == "audio/wav"
        assert result.data == data
        assert self.prompts_content.messages[0]["role"] == "assistant"
        assert self.prompts_content.messages[0]["content"]["type"] == "audio"

    @patch("mcp_serializer.features.prompt.result.FileParser")
    def test_add_file_message_unsupported_mime_type(self, mock_file_parser):
        # Create mock FileMetadata for unsupported file type
        mock_metadata = FileMetadata(
            name="document.pdf",
            size=400,
            mime_type="application/pdf",
            data=base64.b64encode(b"fake_pdf_data").decode("utf-8"),
            content_type="application",
            uri="file://document.pdf",
        )

        # Mock FileParser to return the metadata
        mock_parser_instance = Mock()
        mock_parser_instance.file_metadata = mock_metadata
        mock_file_parser.return_value = mock_parser_instance

        with pytest.raises(ValueError, match="Unsupported content type"):
            self.prompts_content.add_file_message("/path/to/document.pdf")

    @patch("mcp_serializer.features.prompt.result.FileParser")
    def test_add_file_message_parser_failure(self, mock_file_parser):
        # Mock FileParser to raise ValueError
        mock_file_parser.side_effect = ValueError(
            "Cannot determine file type from MimeTypes"
        )

        with pytest.raises(ValueError, match="Unable to process file"):
            self.prompts_content.add_file_message("/path/to/unknown.file")

    def test_add_embedded_resource_with_data(self):
        result = self.prompts_content.add_embedded_resource(
            "https://example.com",
            text="Embedded content",
            mime_type="text/plain",
            role=PromptsResult.Roles.USER,
        )

        assert isinstance(result, EmbeddedResource)
        assert result.resource.text == "Embedded content"
        assert result.resource.mimeType == "text/plain"
        assert self.prompts_content.messages[0]["role"] == "user"

    def test_add_embedded_resource_with_container(self):
        # Create ResourceContainer with content
        resource_container = ResourceContainer()
        resource_content = ResourceResult()
        resource_content.add_text_content("Resource text", "text/plain")

        resource_container.add_resource(
            "file://test.txt", resource_content, name="Test"
        )

        # Create PromptsResult with resource container
        prompts_content = PromptsResult(resource_container=resource_container)
        result = prompts_content.add_embedded_resource("file://test.txt")

        assert isinstance(result, EmbeddedResource)
        assert result.resource.text == "Resource text"
        assert result.resource.name == "Test"

    def test_add_embedded_resource_errors(self):
        # Test without container and without data
        with pytest.raises(PromptsResult.ResourceContainerRequiredError):
            self.prompts_content.add_embedded_resource("file://test.txt")

        # Test without mime type
        with pytest.raises(ValueError, match="Could not determine mime type"):
            self.prompts_content.add_embedded_resource(
                "https://example.com", text="Content without mime type"
            )

    def test_message_role_validation(self):
        # Test invalid role in _add_message (indirectly through add_text)
        with pytest.raises(
            ValueError, match="Role must be either Roles.USER or Roles.ASSISTANT"
        ):
            # This would happen if we could pass invalid role, but our API prevents it
            # Testing the validation exists in the _add_message method
            self.prompts_content._add_message("invalid_role", "content")

    def test_complex_conversation_flow(self):
        """Test a realistic conversation with multiple content types and roles."""
        prompts_content = PromptsResult()

        # User starts conversation
        prompts_content.add_text("Hello, I need help", role=PromptsResult.Roles.USER)

        # Assistant responds
        prompts_content.add_text(
            "I'm happy to help! What do you need?", role=PromptsResult.Roles.ASSISTANT
        )

        # User sends image
        valid_base64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA"
        )
        prompts_content.add_image(
            valid_base64, "image/png", role=PromptsResult.Roles.USER
        )

        # Assistant responds with embedded resource
        prompts_content.add_embedded_resource(
            "https://example.com/help",
            text="Here's a helpful guide",
            mime_type="text/markdown",
            role=PromptsResult.Roles.ASSISTANT,
        )

        assert len(prompts_content.messages) == 4
        assert prompts_content.messages[0]["role"] == "user"
        assert prompts_content.messages[1]["role"] == "assistant"
        assert prompts_content.messages[2]["role"] == "user"
        assert prompts_content.messages[3]["role"] == "assistant"
