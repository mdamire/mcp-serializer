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
        HTM = "text/html"
        XHTML = "application/xhtml+xml"
        MHTML = "multipart/related"
        CSS = "text/css"
        JAVASCRIPT = "text/javascript"
        JSON = "application/json"
        XML = "text/xml"
        SVG = "image/svg+xml"
        MARKDOWN = "text/markdown"
        CSV = "text/csv"
        YAML = "text/yaml"
        PDF = "application/pdf"
        FORM_URLENCODED = "application/x-www-form-urlencoded"
        FORM_DATA = "multipart/form-data"
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
                ".xhtml": cls.XHTML,
                ".xht": cls.XHTML,
                ".mhtml": cls.MHTML,
                ".mht": cls.MHTML,
                ".css": cls.CSS,
                ".js": cls.JAVASCRIPT,
                ".json": cls.JSON,
                ".xml": cls.XML,
                ".svg": cls.SVG,
                ".md": cls.MARKDOWN,
                ".csv": cls.CSV,
                ".yml": cls.YAML,
                ".yaml": cls.YAML,
                ".pdf": cls.PDF,
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

    @classmethod
    def get_mime_type(cls, file_name: str) -> str:
        mime_type = cls.Text.from_file_name(file_name)
        if not mime_type:
            mime_type = cls.Image.from_file_name(file_name)
        if not mime_type:
            mime_type = cls.Audio.from_file_name(file_name)
        return mime_type
