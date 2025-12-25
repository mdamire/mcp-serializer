from typing import get_type_hints, Union, BinaryIO
import inspect
import re
import os
import base64
from .definitions import FunctionMetadata, ArgumentMetadata, FileMetadata, ContentTypes


DEFAULT_TYPE_HINT = str


class FunctionParser:
    """Parse function metadata including name, title, description, arguments, and return type."""

    def __init__(self, func):
        """Initialize with a function to parse.

        Args:
            func: The function to parse
        """
        self.func = func
        self._parsed_docstring = None
        self._signature = None
        self._type_hints = None

        # Initialize metadata container
        self.function_metadata = FunctionMetadata()

        # Parse all components during initialization
        self._parse_components()

    def _parse_components(self):
        """Parse all function components."""
        self._signature = inspect.signature(self.func)
        try:
            self._type_hints = get_type_hints(self.func)
        except (NameError, AttributeError):
            # Handle cases where type hints can't be resolved
            self._type_hints = {}

        self._parsed_docstring = self._parse_docstring_structure(self.func.__doc__)

        # Set parsed properties in metadata
        self.function_metadata.function = self.func
        self.function_metadata.name = self.func.__name__
        self.function_metadata.title = self._parsed_docstring["title"]
        self.function_metadata.description = self._parsed_docstring["description"]
        self.function_metadata.return_type = self._type_hints.get("return")

        self._parse_arguments()

    def _parse_arguments(self):
        """Parse function arguments and populate the arguments list."""
        self.function_metadata.arguments = []

        for param_name, param in self._signature.parameters.items():
            if param_name == "self":
                continue

            arg_metadata = ArgumentMetadata(
                name=param_name,
                type_hint=self._type_hints.get(param_name, DEFAULT_TYPE_HINT),
                description=self._parsed_docstring["params"].get(param_name),
                required=param.default == inspect.Parameter.empty,
                default=param.default
                if param.default != inspect.Parameter.empty
                else FunctionMetadata.empty,
            )
            self.function_metadata.arguments.append(arg_metadata)

    def _parse_docstring_structure(self, docstring):
        """Parse docstring into title, description, and parameters.

        Returns:
            dict with keys: 'title', 'description', 'params'
        """
        if not docstring:
            return {"title": None, "description": None, "params": {}}

        # Split docstring into lines and clean up
        lines = docstring.strip().split("\n")
        lines = [line.rstrip() for line in lines]

        title = None
        description_lines = []
        params = {}

        # Check if first line is title (followed by empty line or end)
        if len(lines) > 1 and lines[1].strip() == "":
            title = lines[0].strip()
            start_idx = 2  # Skip title and empty line
        elif len(lines) == 1:
            title = lines[0].strip()
            start_idx = 1
        else:
            start_idx = 0

        # Find where parameters section starts
        param_start_idx = len(lines)
        param_keywords = ["Args:", "Arguments:", "Parameters:", "Param:"]

        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            if any(line.startswith(keyword) for keyword in param_keywords):
                param_start_idx = i
                break
            # Check for Sphinx style parameters
            if line.startswith(":param"):
                param_start_idx = i
                break
            # Check for NumPy style parameters
            if (
                line == "Parameters"
                and i + 1 < len(lines)
                and re.match(r"^-+$", lines[i + 1].strip())
            ):
                param_start_idx = i
                break

        # Extract description (everything between title and parameters)
        for i in range(start_idx, param_start_idx):
            line = lines[i].strip()
            if line:  # Skip empty lines within description
                description_lines.append(line)

        description = " ".join(description_lines) if description_lines else None

        # Extract parameters from the parameters section
        if param_start_idx < len(lines):
            param_section = "\n".join(lines[param_start_idx:])
            params = self._parse_docstring_params(param_section)

        docstring_info = {"title": title, "description": description, "params": params}
        return docstring_info

    def _parse_docstring_params(self, docstring):
        """Parse parameter descriptions from docstring.
        Supports Google, NumPy, and Sphinx style docstrings.
        """
        if not docstring:
            return {}

        param_descriptions = {}

        # Google style: Args: or Parameters:
        google_match = re.search(
            r"(?:Args?|Arguments?|Parameters?):\s*\n(.*?)(?:\n\n|\n[A-Z]|\Z)",
            docstring,
            re.DOTALL | re.IGNORECASE,
        )
        if google_match:
            params_section = google_match.group(1)
            # Match param_name: description or param_name (type): description
            for match in re.finditer(
                r"^\s*(\w+)(?:\s*\([^)]+\))?\s*:\s*(.+?)(?=^\s*\w+\s*(?:\([^)]+\))?\s*:|$)",
                params_section,
                re.MULTILINE | re.DOTALL,
            ):
                param_name = match.group(1).strip()
                description = re.sub(r"\s+", " ", match.group(2).strip())
                param_descriptions[param_name] = description

        # NumPy style: Parameters followed by dashes
        numpy_match = re.search(
            r"Parameters\s*\n\s*-+\s*\n(.*?)(?:\n+[A-Z][a-z]*\s*\n\s*-+|\Z)",
            docstring,
            re.DOTALL | re.IGNORECASE,
        )
        if numpy_match:
            params_section = numpy_match.group(1)
            # Match param_name : type and description on next lines
            for match in re.finditer(
                r"^\s*(\w+)\s*:.*?\n(.*?)(?=^\s*\w+\s*:|$)",
                params_section,
                re.MULTILINE | re.DOTALL,
            ):
                param_name = match.group(1).strip()
                description = re.sub(r"\s+", " ", match.group(2).strip())
                param_descriptions[param_name] = description

        # Sphinx style: :param param_name: description
        sphinx_matches = re.findall(
            r":param\s+(\w+)\s*:\s*(.+?)(?=\n\s*:|\n\s*\n|\Z)", docstring, re.DOTALL
        )
        for param_name, description in sphinx_matches:
            param_descriptions[param_name.strip()] = re.sub(
                r"\s+", " ", description.strip()
            )

        return param_descriptions


class FileParser:
    """Parse file metadata including name, size, mime type, and content."""

    def __init__(self, file: Union[str, BinaryIO]):
        """Initialize with a file to parse.

        Args:
            file: The file path (str) or file object (BinaryIO) to parse
        """
        self.file = file
        self.file_metadata = self._parse_file()

    def _parse_file(self) -> FileMetadata:
        """Parse the file and extract metadata.

        Returns:
            FileMetadata with content_type set to 'text', 'image', or 'audio'
        """
        # Read file content
        file_name, size, file_content, uri = self._read_file(self.file)

        # Try as text content
        metadata = self._try_as_text_content(file_name, size, file_content, uri)
        if metadata:
            return metadata

        # Try as image content
        metadata = self._try_as_image_content(file_name, size, file_content, uri)
        if metadata:
            return metadata

        # Try as audio content
        metadata = self._try_as_audio_content(file_name, size, file_content, uri)
        if metadata:
            return metadata

        raise ValueError(
            f"Cannot determine file type from MimeTypes for file: {file_name}"
        )

    def _read_file(self, file: Union[str, BinaryIO]) -> tuple[str, int, bytes, str]:
        """Read file and extract file name, size, content, and URI.

        Args:
            file: The file path (str) or file object (BinaryIO)

        Returns:
            Tuple of (file_name, size, file_content, uri)
        """
        if isinstance(file, str):
            file_name = os.path.basename(file)
            size = os.path.getsize(file)
            uri = f"file://{os.path.abspath(file)}"
            with open(file, "rb") as f:
                file_content = f.read()
        else:
            # Handle file-like objects (may be opened or closed)
            file_path = getattr(file, "name", "unknown")
            if hasattr(file_path, "__fspath__"):  # Handle Path objects
                file_name = os.path.basename(file_path.__fspath__())
                uri = f"file://{os.path.abspath(file_path.__fspath__())}"
            elif isinstance(file_path, str) and file_path != "unknown":
                file_name = os.path.basename(file_path)
                uri = f"file://{os.path.abspath(file_path)}"
            else:
                file_name = "unknown"
                uri = None

            should_close = False
            try:
                # Try to use the file as-is (might be already open)
                current_pos = file.tell()
            except (ValueError, AttributeError):
                # File is closed or doesn't support tell()
                if hasattr(file, "open"):
                    file.open("rb")
                    should_close = True
                    current_pos = 0
                else:
                    # Can't open, try reading anyway
                    current_pos = 0

            try:
                # Get size and content
                file.seek(0)
                file_content = file.read()
                size = len(file_content)

                # Restore position only if file supports it
                try:
                    file.seek(current_pos)
                except (ValueError, AttributeError):
                    pass

                if isinstance(file_content, str):
                    file_content = file_content.encode("utf-8")
            finally:
                # Close file if we opened it
                if should_close and hasattr(file, "close"):
                    file.close()

        return file_name, size, file_content, uri

    def _try_as_text_content(
        self, file_name: str, size: int, file_content: bytes, uri: str
    ) -> Union[FileMetadata, None]:
        """Try to process file as text content.

        Args:
            file_name: Name of the file
            size: Size of the file in bytes
            file_content: Raw file content as bytes
            uri: URI of the file

        Returns:
            FileMetadata if successful, None otherwise
        """
        from .contents import MimeTypes

        mime_type = MimeTypes.Text.from_file_name(file_name)
        if mime_type:
            try:
                data = file_content.decode("utf-8")
                return FileMetadata(
                    size=size,
                    name=file_name,
                    mime_type=mime_type,
                    data=data,
                    content_type=ContentTypes.TEXT,
                    uri=uri,
                )
            except UnicodeDecodeError:
                # If it can't be decoded as UTF-8, it's not text
                pass
        return None

    def _try_as_image_content(
        self, file_name: str, size: int, file_content: bytes, uri: str
    ) -> Union[FileMetadata, None]:
        """Try to process file as image content.

        Args:
            file_name: Name of the file
            size: Size of the file in bytes
            file_content: Raw file content as bytes
            uri: URI of the file

        Returns:
            FileMetadata if successful, None otherwise
        """
        from .contents import MimeTypes

        mime_type = MimeTypes.Image.from_file_name(file_name)
        if mime_type:
            data = base64.b64encode(file_content).decode("utf-8")
            return FileMetadata(
                file_name=file_name,
                size=size,
                name=file_name,
                mime_type=mime_type,
                data=data,
                content_type=ContentTypes.IMAGE,
                uri=uri,
            )
        return None

    def _try_as_audio_content(
        self, file_name: str, size: int, file_content: bytes, uri: str
    ) -> Union[FileMetadata, None]:
        """Try to process file as audio content.

        Args:
            file_name: Name of the file
            size: Size of the file in bytes
            file_content: Raw file content as bytes
            uri: URI of the file

        Returns:
            FileMetadata if successful, None otherwise
        """
        from .contents import MimeTypes

        mime_type = MimeTypes.Audio.from_file_name(file_name)
        if mime_type:
            data = base64.b64encode(file_content).decode("utf-8")
            return FileMetadata(
                file_name=file_name,
                size=size,
                name=file_name,
                mime_type=mime_type,
                data=data,
                content_type=ContentTypes.AUDIO,
                uri=uri,
            )
        return None
