from typing import Optional, Dict, Any, Union
from pydantic import BaseModel
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
from ..resource.container import ResourceContainer


class ToolsResult:
    class ResourceNotFoundError(Exception):
        pass

    class ResourceContainerRequiredError(Exception):
        pass

    def __init__(
        self, resource_container: ResourceContainer = None, is_error: bool = False
    ):
        self.content_list = []
        self.resource_container = resource_container
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
        self, file: str, annotations: Optional[Dict[str, Any]] = None
    ) -> Union[TextContent, ImageContent, AudioContent]:
        """Add content from file - automatically detects if it's text, image, or audio.

        Args:
            file: File path or file object
            annotations: Optional annotations

        Returns:
            TextContent, ImageContent, or AudioContent

        Raises:
            ValueError: If file type cannot be determined
        """
        try:
            file_metadata = FileParser(file).file_metadata

            content_kwargs = {
                "annotations": annotations,
            }

            if file_metadata.content_type == ContentTypes.TEXT:
                return self.add_text_content(
                    text=file_metadata.data,
                    **content_kwargs,
                )
            elif file_metadata.content_type == ContentTypes.IMAGE:
                return self.add_image_content(
                    data=file_metadata.data,
                    mime_type=file_metadata.mime_type,
                    **content_kwargs,
                )
            elif file_metadata.content_type == ContentTypes.AUDIO:
                return self.add_audio_content(
                    data=file_metadata.data,
                    mime_type=file_metadata.mime_type,
                    **content_kwargs,
                )
            else:
                raise ValueError(
                    f"Unknown content type: {file_metadata.content_type}"
                )
        except ValueError as e:
            raise ValueError(
                f"Unable to determine data or mime type from file '{file}'. "
                "You can use add_text_content, add_image_content, or add_audio_content methods to add content manually."
            ) from e

    def _get_resource_info(self, uri: str) -> dict:
        if not self.resource_container:
            return {}
        for registry in self.resource_container.schema_assembler.resource_list:
            if registry.uri == uri:
                return registry.extra
        for registry in self.resource_container.schema_assembler.resource_template_list:
            if uri.startswith(registry.uri):
                return registry.extra
        return {}

    def add_resource_link(
        self,
        uri: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        mime_type: Optional[str] = None,
        annotations: Optional[Dict[str, Any]] = None,
    ) -> ResourceLinkContent:
        """Add resource link content.

        For HTTP/HTTPS URIs: ResourceContainer is optional. If not provided, uses default values.
        For non-HTTP URIs: ResourceContainer is required and URI must exist in assembler.
        """
        is_http = uri.startswith(("http://", "https://"))
        if not is_http and not self.resource_container:
            raise self.ResourceContainerRequiredError(
                "Use ResourceContainer to initialize ToolsContent for non-HTTP URIs"
            )

        # get resource registry from resource container resources or resource templates
        resource_info = self._get_resource_info(uri)

        if not resource_info and not is_http:
            raise self.ResourceNotFoundError(
                f"Resource with URI '{uri}' is not found. Define the resource first."
            )

        # Set mime_type with fallbacks
        mime_type = mime_type or resource_info.get("mimeType")
        if not mime_type:
            raise ValueError(
                f"Could not determine mime type for resource link of uri: {uri}, Provide mime type manually."
            )

        resource_link = ResourceLinkContent(
            uri=uri,
            name=name or resource_info.get("name"),
            description=description or resource_info.get("description"),
            mimeType=mime_type,
            annotations=annotations or resource_info.get("annotations"),
        )
        self.content_list.append(resource_link)
        return resource_link

    def add_embedded_resource(
        self,
        uri: str,
        name: Optional[str] = None,
        title: Optional[str] = None,
        mime_type: Optional[str] = None,
        text: Optional[str] = None,
        blob: Optional[str] = None,
        annotations: Optional[Dict[str, Any]] = None,
    ) -> EmbeddedResource:
        """Add embedded resource content."""
        if not text and not blob and not self.resource_container:
            raise self.ResourceContainerRequiredError(
                "Use ResourceContainer to initialize ToolsContent when only URI is provided for embedded resource"
            )

        resource_content = {}
        if self.resource_container:
            try:
                resource_result = self.resource_container.call(uri)
                resource_content = resource_result["contents"][0]
            except Exception:
                if not text and not blob:
                    raise self.ResourceNotFoundError(
                        f"Resource with URI '{uri}' is not found. Either provide text or blob data with mime type."
                    )

        text = text or resource_content.get("text")
        blob = blob or resource_content.get("blob")
        mime_type = mime_type or resource_content.get("mimeType")
        if not mime_type:
            raise ValueError(
                f"Could not determine mime type for embedded resource of uri: {uri}. Provide mime type manually."
            )

        content_data = {
            "uri": uri,
            "mimeType": mime_type,
            "name": name or resource_content.get("name"),
            "title": title or resource_content.get("title"),
            "annotations": annotations or resource_content.get("annotations"),
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

    def add_structured_content(self, content) -> dict:
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
