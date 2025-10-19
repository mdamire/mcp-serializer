import base64
from ..base.contents import (
    ImageContentSanitizer,
    AudioContentSanitizer,
    TextContentSanitizer,
)
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
            uri=uri or "",
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
            uri=uri or "",
            name=name,
            title=title,
            annotations=annotations,
        )
        self.content_list.append(binary_content)
        return binary_content

    def add_file(
        self,
        file: str,
        uri: str = None,
        name: str = None,
        title: str = None,
        annotations: dict = None,
    ):
        # Try text content first
        try:
            sanitized_content = TextContentSanitizer(file=file)
            if sanitized_content.text and sanitized_content.mime_type:
                return self.add_text_content(
                    text=sanitized_content.text,
                    mime_type=sanitized_content.mime_type,
                    uri=uri,
                    name=name,
                    title=title,
                    annotations=annotations,
                )
        except Exception:
            pass

        # Try image content
        try:
            sanitized_content = ImageContentSanitizer(file=file)
            if sanitized_content.data and sanitized_content.mime_type:
                return self.add_binary_content(
                    blob=sanitized_content.data,
                    mime_type=sanitized_content.mime_type,
                    uri=uri,
                    name=name,
                    title=title,
                    annotations=annotations,
                )
        except Exception:
            pass

        # Try audio content
        try:
            sanitized_content = AudioContentSanitizer(file=file)
            if sanitized_content.data and sanitized_content.mime_type:
                return self.add_binary_content(
                    blob=sanitized_content.data,
                    mime_type=sanitized_content.mime_type,
                    uri=uri,
                    name=name,
                    title=title,
                    annotations=annotations,
                )
        except Exception:
            pass

        raise self.FileProcessError(f"Failed to process file: {file}")
