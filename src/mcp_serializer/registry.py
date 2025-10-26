from typing import Union, BinaryIO

from .features.base.parsers import FileParser
from .features.prompt.container import PromptsContainer
from .features.resource.container import ResourceContainer
from .features.prompt.result import PromptsResult
from .features.resource.result import ResourceResult
from .features.tool.container import ToolsContainer


class MCPRegistry:
    def __init__(self):
        self.prompt_container = None
        self.resource_container = None
        self.tools_container = None

    def _get_prompt_container(self):
        if self.prompt_container is None:
            self.prompt_container = PromptsContainer()
        return self.prompt_container

    def _get_resource_container(self):
        if self.resource_container is None:
            self.resource_container = ResourceContainer()
        return self.resource_container

    def _get_tools_container(self):
        if self.tools_container is None:
            self.tools_container = ToolsContainer()
        return self.tools_container

    def resource(
        self,
        uri: str,
        annotations=None,
        **extra,
    ):
        def decorator(func):
            self._get_resource_container().register(
                func,
                uri,
                annotations=annotations,
                **extra,
            )
            return func

        return decorator

    def add_file_resource(
        self,
        file: Union[str, BinaryIO],
        uri: str = None,
        title: str = None,
        description: str = None,
        annotations: dict = None,
    ):
        file_metadata = FileParser(file).file_metadata
        uri = uri or file_metadata.uri
        if not uri:
            raise ValueError(
                "Could not determine URI for file. Provide uri as parameter."
            )

        result = ResourceResult()
        result._add_file_metadata(file_metadata)

        return self._get_resource_container().add_resource(
            result=result,
            uri=uri,
            name=file_metadata.name,
            mime_type=file_metadata.mime_type,
            size=file_metadata.size,
            title=title,
            description=description,
            annotations=annotations,
        )

    def add_http_resource(
        self,
        uri: str,
        name: str = None,
        title: str = None,
        description: str = None,
        mime_type: str = None,
        size: int = None,
        annotations: dict = None,
    ):
        if not uri.startswith(("http://", "https://")):
            raise ValueError("URI must start with http:// or https://")

        return self._get_resource_container().add_resource(
            uri=uri,
            name=name,
            mime_type=mime_type,
            title=title,
            description=description,
            size=size,
            annotations=annotations,
        )

    def prompt(self, name=None, title=None, description=None):
        def decorator(func):
            self._get_prompt_container().register(
                func, name=name, title=title, description=description
            )
            return func

        return decorator

    def add_text_prompt(
        self,
        name: str,
        text: str,
        role: str = None,
        mime_type: str = None,
        title: str = None,
        description: str = None,
    ):
        """Add a text-based prompt with static content."""
        prompt = self._get_prompt_container().add_text_prompt(
            name=name,
            text=text,
            role=role,
            mime_type=mime_type,
            title=title,
            description=description,
        )
        return prompt

    def add_file_prompt(
        self,
        name: str,
        file: Union[str, BinaryIO],
        role: str = None,
        title: str = None,
        description: str = None,
    ):
        """Add a file-based prompt by automatically determining its type."""
        prompt = self._get_prompt_container().add_file_prompt(
            name=name,
            file=file,
            role=role,
            title=title,
            description=description,
        )
        return prompt

    def tool(self, name=None, title=None, description=None, annotations=None):
        def decorator(func):
            self._get_tools_container().register(
                func,
                name=name,
                title=title,
                description=description,
                annotations=annotations,
            )
            return func

        return decorator
