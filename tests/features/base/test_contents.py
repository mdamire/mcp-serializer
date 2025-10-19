from mcp_serializer.features.base.contents import MimeTypes


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
