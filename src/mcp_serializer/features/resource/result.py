import base64
from ..base.parsers import FileParser
from ..base.definitions import ContentTypes, FileMetadata
from .schema import TextContentSchema, BinaryContentSchema


class ResourceResult:
    class FileProcessError(Exception):
        pass

    def __init__(self):
        self.content_list = []

    def add_text_content(
        self,
        text: str,
        mime_type: str = None,
        uri: str = None,
        name: str = None,
        title: str = None,
        annotations: dict = None,
    ):
        # Validate base64 if needed for blob
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")

        text_content = TextContentSchema(
            text=text,
            mimeType=mime_type,
            uri=uri,
            name=name,
            title=title,
            annotations=annotations,
        )
        self.content_list.append(text_content)
        return text_content

    def add_binary_content(
        self,
        blob: str,
        mime_type: str = None,
        uri: str = None,
        name: str = None,
        title: str = None,
        annotations: dict = None,
    ):
        # Validate base64 format
        if not blob or not isinstance(blob, str):
            raise ValueError("Blob must be a non-empty string")
        try:
            base64.b64decode(blob, validate=True)
        except Exception:
            raise ValueError("Blob must be valid base64 encoded data")

        binary_content = BinaryContentSchema(
            blob=blob,
            mimeType=mime_type,
            uri=uri,
            name=name,
            title=title,
            annotations=annotations,
        )
        self.content_list.append(binary_content)
        return binary_content

    def _add_file_metadata(
        self,
        file_metadata: FileMetadata,
        uri=None,
        name=None,
        title=None,
        annotations=None,
    ):
        content_kwargs = {
            "uri": uri or file_metadata.uri,
            "mime_type": file_metadata.mime_type,
            "name": name or file_metadata.name,
            "title": title,
            "annotations": annotations,
        }

        if file_metadata.content_type == ContentTypes.TEXT:
            return self.add_text_content(
                text=file_metadata.data,
                **content_kwargs,
            )
        elif file_metadata.content_type in (ContentTypes.IMAGE, ContentTypes.AUDIO):
            return self.add_binary_content(
                blob=file_metadata.data,
                **content_kwargs,
            )
        else:
            raise self.FileProcessError(
                f"Could not determine content type for file: {file_metadata.name}. "
                "You can use add_text_content or add_binary_content to add content manually."
            )

    def add_file(
        self,
        file: str,
        uri: str = None,
        name: str = None,
        title: str = None,
        annotations: dict = None,
    ):
        """Add file content by automatically determining its type.

        Args:
            file: File path or file object
            uri: Optional URI for the content
            name: Optional name for the content
            title: Optional title for the content
            annotations: Optional annotations

        Returns:
            TextContentSchema or BinaryContentSchema

        Raises:
            FileProcessError: If file type cannot be determined
        """
        try:
            file_metadata = FileParser(file).file_metadata
        except ValueError as e:
            raise self.FileProcessError(
                f"Failed to parse file metadata. You can use add_text_content or add_binary_content"
                " to add content manually."
            ) from e
        return self._add_file_metadata(file_metadata, uri, name, title, annotations)
