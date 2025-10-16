from .features.prompt.container import PromptsContainer
from .features.resource.container import ResourceContainer
from .features.resource.contents import ResourceContent
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
        uri,
        name=None,
        title=None,
        description=None,
        mime_type=None,
        size=None,
        annotations=None,
    ):
        def decorator(func):
            self._get_resource_container().register(
                func,
                uri,
                name=name,
                title=title,
                description=description,
                mime_type=mime_type,
                size=size,
                annotations=annotations,
            )
            return func

        return decorator

    def add_resource(
        self,
        uri,
        content: ResourceContent=None,
        name=None,
        title=None,
        description=None,
        mime_type=None,
        size=None,
        annotations=None,
    ):
        return self._get_resource_container().add_resource(
            uri,
            content,
            name=name,
            title=title,
            description=description,
            mime_type=mime_type,
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
