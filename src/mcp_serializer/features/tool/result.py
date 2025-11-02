from typing import Optional, Dict, Any, Union
from pydantic import BaseModel
from urllib.parse import urlparse
from ..base.contents import MimeTypes
from ..base.parsers import FileParser
from ..base.definitions import ContentTypes
from .schema import (
    TextContent,
    ImageContent,
    AudioContent,
    ResourceLinkContent,
    EmbeddedResource,
)
from ..resource.schema import TextContentSchema, BinaryContentSchema


class ToolsResult:
    def __init__(self, is_error: bool = False):
        self.content_list = []
        self.structured_content = None
        self.is_error = is_error

    def add_text_content(
        self, text: str, annotations: Optional[Dict[str, Any]] = None
    ) -> TextContent:
        """Add text content."""
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")

        text_content = TextContent(text=text, annotations=annotations)
        self.content_list.append(text_content)
        return text_content

    def add_image_content(
        self,
        data: str,
        mime_type: Optional[str] = None,
        annotations: Optional[Dict[str, Any]] = None,
    ) -> ImageContent:
        """Add image content with base64 data."""
        if not data or not isinstance(data, str):
            raise ValueError("Data must be a non-empty string")

        image_content = ImageContent(
            data=data, mimeType=mime_type, annotations=annotations
        )
        self.content_list.append(image_content)
        return image_content

    def add_audio_content(
        self,
        data: str,
        mime_type: Optional[str] = None,
        annotations: Optional[Dict[str, Any]] = None,
    ) -> AudioContent:
        """Add audio content with base64 data."""
        if not data or not isinstance(data, str):
            raise ValueError("Data must be a non-empty string")

        audio_content = AudioContent(
            data=data, mimeType=mime_type, annotations=annotations
        )
        self.content_list.append(audio_content)
        return audio_content

    def add_file(
        self,
        file: str,
        uri: Optional[str] = None,
        name: Optional[str] = None,
        title: Optional[str] = None,
        annotations: Optional[Dict[str, Any]] = None,
    ) -> Union[TextContent, ImageContent, AudioContent]:
        try:
            file_metadata = FileParser(file).file_metadata
        except ValueError as e:
            raise ValueError(
                f"Unable to determine data or mime type from file '{file}'. You can use add_text_content, "
                "add_image_content or add_audio_content methods to add content manually."
            ) from e

        if file_metadata.content_type == ContentTypes.TEXT:
            text = file_metadata.data
            blob = None
        else:
            blob = file_metadata.data
            text = None

        embedded_resource = self.add_embedded_resource(
            uri=uri or file_metadata.uri,
            text=text,
            blob=blob,
            mime_type=file_metadata.mime_type,
            name=name or file_metadata.name,
            title=title,
            annotations=annotations,
        )
        return embedded_resource

    def _get_resource_registry(self, uri: str, registry):
        resource_container = registry.resource_container
        if not resource_container:
            raise ValueError("No resource has been defined for this registry")

        # get from resource list
        for resource_registry in resource_container.schema_assembler.resource_list:
            if resource_registry.uri.rstrip("/") == uri.rstrip("/"):
                return resource_registry

        # get from resource template list
        for (
            resource_template_registry
        ) in resource_container.schema_assembler.resource_template_list:
            if uri.startswith(resource_template_registry.uri):
                return resource_template_registry

        # to do get http resource info from resource container's assembler

        return None

    def _get_mime_type_from_http_uri(self, uri: str) -> str:
        try:
            url_path = urlparse(uri).path
            return MimeTypes.get_mime_type(url_path)
        except Exception:
            return None

    def add_resource_link(
        self,
        uri: str,
        registry=None,
        name: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        mime_type: Optional[str] = None,
        annotations: Optional[Dict[str, Any]] = None,
    ) -> ResourceLinkContent:
        is_http = uri.startswith(("http://", "https://"))
        if is_http:
            mime_type = mime_type or self._get_mime_type_from_http_uri(uri)
        elif not registry:
            raise ValueError("registry is required for non-HTTP URIs")

        resource_registry = None
        if registry:
            resource_registry = self._get_resource_registry(uri, registry)
            if not is_http and not resource_registry:
                raise ValueError(
                    f"Resource with URI '{uri}' is not found. Define the resource first."
                )

        if resource_registry:
            name = name or resource_registry.extra.get("name")
            title = title or resource_registry.extra.get("title")
            description = description or resource_registry.extra.get("description")
            mime_type = mime_type or resource_registry.extra.get("mime_type")
            annotations = annotations or resource_registry.extra.get("annotations")

            if hasattr(resource_registry, "metadata"):
                name = name or resource_registry.metadata.name
                title = title or resource_registry.metadata.title
                description = description or resource_registry.metadata.description

        resource_link = ResourceLinkContent(
            uri=uri,
            name=name,
            title=title,
            description=description,
            mimeType=mime_type,
            annotations=annotations,
        )
        self.content_list.append(resource_link)
        return resource_link

    def add_embedded_resource(
        self,
        uri: str,
        text: Optional[str] = None,
        blob: Optional[str] = None,
        mime_type: Optional[str] = None,
        name: Optional[str] = None,
        title: Optional[str] = None,
        annotations: Optional[Dict[str, Any]] = None,
    ) -> EmbeddedResource:
        """Add embedded resource content."""
        if not text and not blob:
            raise ValueError(
                "Either 'text' or 'blob' must be provided for embedded resource."
            )

        content_data = {
            "uri": uri,
            "mimeType": mime_type,
            "name": name,
            "title": title,
            "annotations": annotations,
        }

        # Create appropriate schema based on content type
        if text:
            resource_schema = TextContentSchema(
                text=text,
                **content_data,
            )
        elif blob:
            resource_schema = BinaryContentSchema(
                blob=blob,
                **content_data,
            )
        else:
            raise ValueError(
                "Either 'text' or 'blob' must be provided for embedded resource"
            )

        embedded_resource = EmbeddedResource(resource=resource_schema)
        self.content_list.append(embedded_resource)
        return embedded_resource

    def add_structured_content(self, content: Union[BaseModel, dict]) -> dict:
        """Add structured content from Pydantic model or dictionary."""
        if isinstance(content, BaseModel):
            content_dict = content.model_dump()
        elif isinstance(content, dict):
            content_dict = content
        else:
            raise ValueError("Content must be a valid Pydantic model or dictionary")

        if self.structured_content:
            raise ValueError("Structured content already exists")

        self.structured_content = content_dict
        return content_dict
