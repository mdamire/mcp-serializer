from typing import Union, BinaryIO
import os
import base64
from enum import Enum


class MimeTypeMapper(Enum):
    @classmethod
    def _get_file_name_extension(cls, file_name: str) -> str:
        _, ext = os.path.splitext(file_name)
        return ext.lower()

    @classmethod
    def _get_file_extension_mapping(cls) -> dict:
        pass

    @classmethod
    def from_file_name(cls, file_name: str) -> str:
        ext = cls._get_file_name_extension(file_name)
        return cls._get_file_extension_mapping().get(ext, None)


class MimeTypes:
    class Image(MimeTypeMapper):
        PNG = "image/png"
        JPEG = "image/jpeg"
        JPG = "image/jpeg"  # Alias for JPEG
        GIF = "image/gif"
        WEBP = "image/webp"
        BMP = "image/bmp"
        SVG = "image/svg+xml"
        TIFF = "image/tiff"

        @classmethod
        def _get_file_extension_mapping(cls) -> dict:
            mapping = {
                ".png": cls.PNG,
                ".jpg": cls.JPEG,
                ".jpeg": cls.JPEG,
                ".gif": cls.GIF,
                ".webp": cls.WEBP,
                ".bmp": cls.BMP,
                ".svg": cls.SVG,
                ".tiff": cls.TIFF,
                ".tif": cls.TIFF,
            }
            return mapping

    class Audio(MimeTypeMapper):
        WAV = "audio/wav"
        MP3 = "audio/mpeg"
        AAC = "audio/aac"
        OGG = "audio/ogg"
        FLAC = "audio/flac"
        M4A = "audio/mp4"
        WMA = "audio/x-ms-wma"
        OPUS = "audio/opus"
        WEBM = "audio/webm"

        @classmethod
        def _get_file_extension_mapping(cls) -> dict:
            mapping = {
                ".wav": cls.WAV,
                ".mp3": cls.MP3,
                ".aac": cls.AAC,
                ".ogg": cls.OGG,
                ".oga": cls.OGG,  # Alternative OGG extension
                ".flac": cls.FLAC,
                ".m4a": cls.M4A,
                ".mp4": cls.M4A,  # MP4 audio
                ".wma": cls.WMA,
                ".opus": cls.OPUS,
                ".webm": cls.WEBM,
            }
            return mapping

    class Text(MimeTypeMapper):
        PLAIN = "text/plain"
        HTML = "text/html"
        CSS = "text/css"
        JAVASCRIPT = "text/javascript"
        JSON = "application/json"
        XML = "text/xml"
        MARKDOWN = "text/markdown"
        CSV = "text/csv"
        YAML = "text/yaml"
        PYTHON = "text/x-python"
        JAVA = "text/x-java"
        CPP = "text/x-c++src"
        C = "text/x-csrc"
        SHELL = "text/x-shellscript"
        SQL = "text/x-sql"
        PHP = "text/x-php"
        RUBY = "text/x-ruby"
        GO = "text/x-go"
        RUST = "text/x-rust"
        TYPESCRIPT = "text/x-typescript"

        @classmethod
        def _get_file_extension_mapping(cls) -> dict:
            mapping = {
                ".txt": cls.PLAIN,
                ".html": cls.HTML,
                ".htm": cls.HTML,
                ".css": cls.CSS,
                ".js": cls.JAVASCRIPT,
                ".json": cls.JSON,
                ".xml": cls.XML,
                ".md": cls.MARKDOWN,
                ".csv": cls.CSV,
                ".yml": cls.YAML,
                ".yaml": cls.YAML,
                ".py": cls.PYTHON,
                ".java": cls.JAVA,
                ".cpp": cls.CPP,
                ".cxx": cls.CPP,
                ".c": cls.C,
                ".sh": cls.SHELL,
                ".sql": cls.SQL,
                ".php": cls.PHP,
                ".rb": cls.RUBY,
                ".go": cls.GO,
                ".rs": cls.RUST,
                ".ts": cls.TYPESCRIPT,
            }
            return mapping


class BinaryContentSanitizer:
    _mime_type_mapper_class: MimeTypeMapper = None

    def __init__(
        self,
        data: Union[str, bytes] = None,
        mime_type: str = None,
        file: Union[str, BinaryIO] = None,
        **kwargs,
    ):
        self.data = None
        self.mime_type = mime_type
        self.file = file

        if data is not None:
            self.data = self._validate_and_encode_data(data)
        if file is not None:
            self.data, file_mime_type = self._process_file_input(file)
            if not self.mime_type:
                self.mime_type = file_mime_type

        if self.data is None:
            if file:
                msg = "Could not create binary content data from file. Provide data as an argument."
            else:
                msg = "Provide data of binary content as an argument or provide a valid file."
            raise ValueError(msg)

        if not self.mime_type:
            if file:
                msg = "Could not determine mime type of binary content from file. Provide a mime type as an argument."
            else:
                msg = "Provide a mime type of binary content as an argument."
            raise ValueError(msg)

    def _process_file_input(self, file: Union[str, BinaryIO]):
        file_content, file_name = self._read_file(file)
        data = self._encode_to_base64(file_content)
        mime_type = self._get_mime_type_from_file_name(file_name)
        return data, mime_type

    def _read_file(self, file: Union[str, BinaryIO]) -> tuple[bytes, str]:
        """Read file content from either file path or file object."""
        if isinstance(file, str):
            with open(file, "rb") as f:
                file_content = f.read()
            return file_content, file
        else:
            file_content = file.read()
            file_name = getattr(file, "name", None)
            return file_content, file_name

    def _validate_and_encode_data(self, data: Union[str, bytes]) -> str:
        if isinstance(data, bytes):
            return self._process_bytes_data(data)
        elif isinstance(data, str):
            return self._process_string_data(data)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

    def _process_bytes_data(self, data: bytes) -> str:
        try:
            base64.b64decode(data, validate=True)
            return data.decode("utf-8")
        except Exception:
            return self._encode_to_base64(data)

    def _process_string_data(self, data: str) -> str:
        try:
            base64.b64decode(data, validate=True)
            return data
        except Exception:
            return self._encode_to_base64(data.encode("utf-8"))

    def _encode_to_base64(self, data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")

    def _get_mime_type_from_file_name(self, file_name: str) -> str:
        if self._mime_type_mapper_class is None:
            return None
        return self._mime_type_mapper_class.from_file_name(file_name)


class ImageContentSanitizer(BinaryContentSanitizer):
    _mime_type_mapper_class = MimeTypes.Image


class AudioContentSanitizer(BinaryContentSanitizer):
    _mime_type_mapper_class = MimeTypes.Audio


class TextContentSanitizer:
    def __init__(
        self,
        text: str = None,
        mime_type: str = None,
        file: Union[str, BinaryIO] = None,
        **kwargs,
    ):
        self.text = None
        self.mime_type = mime_type
        self.file = file

        if text is not None:
            self.text = self._validate_text_data(text)
        if file is not None:
            self.text, file_mime_type = self._process_file_input(file)
            if not self.mime_type:
                self.mime_type = file_mime_type

        if self.text is None:
            if file:
                msg = "Could not create text content data from file. Provide data as an argument."
            else:
                msg = "Provide data of text content as an argument or provide a valid file."
            raise ValueError(msg)

        if not self.mime_type:
            if file:
                msg = "Could not determine mime type of text content from file. Provide a mime type as an argument."
            else:
                msg = "Provide a mime type of text content as an argument."
            raise ValueError(msg)

    def _validate_text_data(self, text: str) -> str:
        if not isinstance(text, str):
            raise ValueError("Text must be a string")
        return text

    def _process_file_input(self, file: Union[str, BinaryIO]):
        file_content, file_name = self._read_file(file)
        text = file_content.decode("utf-8")
        mime_type = self._get_mime_type_from_file_name(file_name)
        return text, mime_type

    def _read_file(self, file: Union[str, BinaryIO]) -> tuple[bytes, str]:
        """Read file content from either file path or file object."""
        if isinstance(file, str):
            with open(file, "rb") as f:
                file_content = f.read()
            return file_content, file
        else:
            file_content = file.read()
            file_name = getattr(file, "name", None)
            return file_content, file_name

    def _get_mime_type_from_file_name(self, file_name: str) -> str:
        return MimeTypes.Text.from_file_name(file_name)
