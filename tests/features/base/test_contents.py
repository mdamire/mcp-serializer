import base64
import tempfile
import io
import pytest
from pathlib import Path
from mcp_serializer.features.base.contents import (
    MimeTypes,
    BinaryContentSanitizer,
    ImageContentSanitizer,
    AudioContentSanitizer,
    TextContentSanitizer,
)


class TestMimeTypes:
    def test_image_mime_type_mapping(self):
        test_cases = [
            ("image.png", MimeTypes.Image.PNG),
            ("photo.jpg", MimeTypes.Image.JPEG),
            ("avatar.jpeg", MimeTypes.Image.JPEG),
            ("icon.gif", MimeTypes.Image.GIF),
            ("banner.webp", MimeTypes.Image.WEBP),
            ("logo.svg", MimeTypes.Image.SVG),
            ("scan.tiff", MimeTypes.Image.TIFF),
            ("document.tif", MimeTypes.Image.TIFF),
        ]

        for filename, expected_mime in test_cases:
            result = MimeTypes.Image.from_file_name(filename)
            assert result == expected_mime, f"Failed for {filename}"
            assert result.value.startswith("image/")

    def test_audio_mime_type_mapping(self):
        test_cases = [
            ("song.mp3", MimeTypes.Audio.MP3),
            ("voice.wav", MimeTypes.Audio.WAV),
            ("track.flac", MimeTypes.Audio.FLAC),
            ("music.m4a", MimeTypes.Audio.M4A),
            ("audio.ogg", MimeTypes.Audio.OGG),
            ("sound.oga", MimeTypes.Audio.OGG),
            ("speech.opus", MimeTypes.Audio.OPUS),
        ]

        for filename, expected_mime in test_cases:
            result = MimeTypes.Audio.from_file_name(filename)
            assert result == expected_mime, f"Failed for {filename}"
            assert result.value.startswith("audio/")

    def test_text_mime_type_mapping(self):
        test_cases = [
            ("document.txt", MimeTypes.Text.PLAIN),
            ("page.html", MimeTypes.Text.HTML),
            ("page.htm", MimeTypes.Text.HTML),
            ("style.css", MimeTypes.Text.CSS),
            ("script.js", MimeTypes.Text.JAVASCRIPT),
            ("data.json", MimeTypes.Text.JSON),
            ("readme.md", MimeTypes.Text.MARKDOWN),
            ("config.yml", MimeTypes.Text.YAML),
            ("config.yaml", MimeTypes.Text.YAML),
            ("main.py", MimeTypes.Text.PYTHON),
            ("App.java", MimeTypes.Text.JAVA),
            ("program.cpp", MimeTypes.Text.CPP),
            ("script.sh", MimeTypes.Text.SHELL),
            ("query.sql", MimeTypes.Text.SQL),
            ("main.rs", MimeTypes.Text.RUST),
            ("app.ts", MimeTypes.Text.TYPESCRIPT),
        ]

        for filename, expected_mime in test_cases:
            result = MimeTypes.Text.from_file_name(filename)
            assert result == expected_mime, f"Failed for {filename}"

    def test_unknown_file_extension_returns_none(self):
        unknown_files = ["file.unknown", "test.xyz", "data.rare"]

        for filename in unknown_files:
            assert MimeTypes.Image.from_file_name(filename) is None
            assert MimeTypes.Audio.from_file_name(filename) is None
            assert MimeTypes.Text.from_file_name(filename) is None

    def test_case_insensitive_extension_mapping(self):
        assert MimeTypes.Image.from_file_name("photo.PNG") == MimeTypes.Image.PNG
        assert MimeTypes.Audio.from_file_name("song.MP3") == MimeTypes.Audio.MP3
        assert MimeTypes.Text.from_file_name("script.PY") == MimeTypes.Text.PYTHON


class TestBinaryContentSanitizer:
    def test_init_with_raw_bytes_data(self):
        raw_data = b"hello world"
        sanitizer = BinaryContentSanitizer(data=raw_data, mime_type="text/plain")

        expected_b64 = base64.b64encode(raw_data).decode("utf-8")
        assert sanitizer.data == expected_b64
        assert sanitizer.mime_type == "text/plain"

    def test_init_with_base64_string_data(self):
        raw_data = b"test data"
        b64_data = base64.b64encode(raw_data).decode("utf-8")

        sanitizer = BinaryContentSanitizer(data=b64_data, mime_type="text/plain")
        assert sanitizer.data == b64_data
        assert sanitizer.mime_type == "text/plain"

    def test_init_with_non_base64_string_converts_to_base64(self):
        text_data = "plain text string"
        sanitizer = BinaryContentSanitizer(data=text_data, mime_type="text/plain")

        expected_b64 = base64.b64encode(text_data.encode("utf-8")).decode("utf-8")
        assert sanitizer.data == expected_b64
        assert sanitizer.mime_type == "text/plain"

    def test_init_with_file_path(self):
        test_content = b"file content for testing"

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        with pytest.raises(
            ValueError,
            match="Could not determine mime type of binary content from file. Provide a mime type as an argument.",
        ):
            BinaryContentSanitizer(file=temp_file_path)

    def test_init_with_file_object(self):
        test_content = b"binary file content"
        file_obj = io.BytesIO(test_content)
        file_obj.name = "test.bin"

        sanitizer = BinaryContentSanitizer(
            file=file_obj, mime_type="application/octet-stream"
        )
        expected_b64 = base64.b64encode(test_content).decode("utf-8")
        assert sanitizer.data == expected_b64
        assert sanitizer.mime_type == "application/octet-stream"

    def test_error_when_no_data_or_file_provided(self):
        with pytest.raises(ValueError, match="Provide data of binary content"):
            BinaryContentSanitizer(mime_type="text/plain")

    def test_error_when_no_mime_type_provided(self):
        with pytest.raises(ValueError, match="Provide a mime type of binary content"):
            BinaryContentSanitizer(data=b"test data")

    def test_unsupported_data_type_raises_error(self):
        with pytest.raises(ValueError, match="Unsupported data type"):
            BinaryContentSanitizer(data=123, mime_type="text/plain")


class TestImageContentSanitizer:
    def test_auto_detect_mime_type_from_image_file(self):
        test_content = b"fake png content"

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            sanitizer = ImageContentSanitizer(file=temp_file_path)
            expected_b64 = base64.b64encode(test_content).decode("utf-8")
            assert sanitizer.data == expected_b64
            assert sanitizer.mime_type == MimeTypes.Image.PNG
        finally:
            Path(temp_file_path).unlink()

    def test_manual_mime_type_overrides_detection(self):
        test_content = b"custom image data"

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            sanitizer = ImageContentSanitizer(
                file=temp_file_path, mime_type="image/custom"
            )
            assert sanitizer.mime_type == "image/custom"
        finally:
            Path(temp_file_path).unlink()


class TestAudioContentSanitizer:
    def test_auto_detect_mime_type_from_audio_file(self):
        test_content = b"fake mp3 content"

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            sanitizer = AudioContentSanitizer(file=temp_file_path)
            expected_b64 = base64.b64encode(test_content).decode("utf-8")
            assert sanitizer.data == expected_b64
            assert sanitizer.mime_type == MimeTypes.Audio.MP3
        finally:
            Path(temp_file_path).unlink()


class TestTextContentSanitizer:
    def test_init_with_text_string(self):
        test_text = "Hello, world! This is a test."
        sanitizer = TextContentSanitizer(text=test_text, mime_type="text/plain")

        assert sanitizer.text == test_text
        assert sanitizer.mime_type == "text/plain"

    def test_init_with_text_file_path(self):
        test_content = "Content from file\nSecond line"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            sanitizer = TextContentSanitizer(file=temp_file_path)
            assert sanitizer.text == test_content
            assert sanitizer.mime_type == MimeTypes.Text.PLAIN
        finally:
            Path(temp_file_path).unlink()

    def test_init_with_text_file_object(self):
        test_content = "File object content"
        file_obj = io.StringIO(test_content)
        file_obj.name = "test.py"

        # Convert to bytes for the sanitizer
        byte_obj = io.BytesIO(test_content.encode("utf-8"))
        byte_obj.name = "test.py"

        sanitizer = TextContentSanitizer(file=byte_obj)
        assert sanitizer.text == test_content
        assert sanitizer.mime_type == MimeTypes.Text.PYTHON

    def test_auto_detect_mime_type_from_file_extension(self):
        file_types = [
            (".py", MimeTypes.Text.PYTHON),
            (".js", MimeTypes.Text.JAVASCRIPT),
            (".html", MimeTypes.Text.HTML),
            (".md", MimeTypes.Text.MARKDOWN),
            (".json", MimeTypes.Text.JSON),
        ]

        for ext, expected_mime in file_types:
            test_content = f"# Content for {ext} file"

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=ext, delete=False, encoding="utf-8"
            ) as temp_file:
                temp_file.write(test_content)
                temp_file_path = temp_file.name

            try:
                sanitizer = TextContentSanitizer(file=temp_file_path)
                assert sanitizer.mime_type == expected_mime
                assert sanitizer.text == test_content
            finally:
                Path(temp_file_path).unlink()

    def test_error_when_no_text_or_file_provided(self):
        with pytest.raises(ValueError, match="Provide data of text content"):
            TextContentSanitizer(mime_type="text/plain")

    def test_error_when_no_mime_type_provided(self):
        with pytest.raises(ValueError, match="Provide a mime type of text content"):
            TextContentSanitizer(text="sample text")

    def test_invalid_text_type_raises_error(self):
        with pytest.raises(ValueError, match="Text must be a string"):
            TextContentSanitizer(text=123, mime_type="text/plain")

    def test_manual_mime_type_overrides_detection(self):
        test_content = "Python-looking content"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            sanitizer = TextContentSanitizer(
                file=temp_file_path, mime_type="text/custom"
            )
            assert sanitizer.mime_type == "text/custom"
            assert sanitizer.text == test_content
        finally:
            Path(temp_file_path).unlink()


class TestEdgeCases:
    def test_empty_file_handling(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file_path = temp_file.name  # Empty file

        try:
            # Empty binary file
            sanitizer = BinaryContentSanitizer(
                file=temp_file_path, mime_type="text/plain"
            )
            expected_b64 = base64.b64encode(b"").decode("utf-8")
            assert sanitizer.data == expected_b64

            # Empty text file
            text_sanitizer = TextContentSanitizer(
                file=temp_file_path, mime_type="text/plain"
            )
            assert text_sanitizer.text == ""
        finally:
            Path(temp_file_path).unlink()

    def test_file_object_without_name_attribute(self):
        test_content = b"content without name"
        file_obj = io.BytesIO(test_content)
        # file_obj.name is not set

        sanitizer = BinaryContentSanitizer(
            file=file_obj, mime_type="application/octet-stream"
        )
        expected_b64 = base64.b64encode(test_content).decode("utf-8")
        assert sanitizer.data == expected_b64
        assert sanitizer.mime_type == "application/octet-stream"
