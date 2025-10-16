from typing import Optional

from .schema import (
    ResourceListResultSchema,
    ResourceTemplateListResultSchema,
    ResourceDefinitionSchema,
)
from .contents import ResourceContent
from .schema import ContentSchema
from ..base.assembler import FeatureSchemaAssembler
from ..base.pagination import Pagination


class ResourceSchemaAssembler(FeatureSchemaAssembler):
    def __init__(self):
        self.resource_list = []
        self.resource_template_list = []

    def add_resource_registry(self, resource_registry):
        from .container import FunctionRegistry

        if (
            isinstance(resource_registry, FunctionRegistry)
            and resource_registry.metadata.has_arguments
        ):
            self._append_sorted_list(
                self.resource_template_list, resource_registry, "uri"
            )
        else:
            self._append_sorted_list(self.resource_list, resource_registry, "uri")

    def _build_function_uri(self, function_registry):
        uri = function_registry.uri
        for argument in function_registry.metadata.arguments:
            if argument.required:
                uri += "/{" + argument.name + "}"
        return uri

    def _build_definition_schema(self, resource_registry_list):
        from .container import FunctionRegistry

        resource_schema_list = []
        for resource_registry in resource_registry_list:
            definition_kwargs = {}
            if isinstance(resource_registry, FunctionRegistry):
                metadata = resource_registry.metadata
                definition_kwargs = {
                    "uri": self._build_function_uri(resource_registry),
                    "name": resource_registry.extra.get("name") or metadata.name,
                    "title": resource_registry.extra.get("title") or metadata.title,
                    "description": resource_registry.extra.get("description")
                    or metadata.description,
                    "mimeType": resource_registry.extra.get("mime_type"),
                    "size": resource_registry.extra.get("size"),
                    "annotations": self._remove_none_from_dict(
                        resource_registry.extra.get("annotations")
                    ),
                }
            else:
                definition_kwargs = {
                    "uri": resource_registry.uri,
                    "name": resource_registry.extra.get("name"),
                    "title": resource_registry.extra.get("title"),
                    "description": resource_registry.extra.get("description"),
                    "mimeType": resource_registry.extra.get("mime_type"),
                    "size": resource_registry.extra.get("size"),
                    "annotations": self._remove_none_from_dict(
                        resource_registry.extra.get("annotations")
                    ),
                }

            # build definition schema
            definition_schema = ResourceDefinitionSchema(**definition_kwargs)

            # add metadata to definition_schema
            resource_schema_list.append(self._build_non_none_dict(definition_schema))

        return resource_schema_list

    def build_list_result_schema(
        self, page_size: int = 10, cursor: Optional[str] = None
    ):
        resource_schema_list = self._build_definition_schema(self.resource_list)
        pagination = Pagination(page_size)
        paginated_resource_schema_list, next_cursor = pagination.paginate(
            resource_schema_list, cursor
        )
        schema = ResourceListResultSchema(
            resources=paginated_resource_schema_list, nextCursor=next_cursor
        )
        schema = self._build_non_none_dict(schema)
        return schema

    def build_template_list_result_schema(
        self, page_size: int = 10, cursor: Optional[str] = None
    ):
        resource_template_schema_list = self._build_definition_schema(
            self.resource_template_list
        )
        pagination = Pagination(page_size)
        paginated_template_schema_list, next_cursor = pagination.paginate(
            resource_template_schema_list, cursor
        )
        schema = ResourceTemplateListResultSchema(
            resourceTemplates=paginated_template_schema_list, nextCursor=next_cursor
        )
        schema = self._build_non_none_dict(schema)
        return schema

    def process_content(self, resource_content, resource_registry):
        if not isinstance(resource_content, ResourceContent):
            raise self.UnsupportedResultTypeError(type(resource_content))

        content_schema_list = []
        for content in resource_content.content_list:
            updated_content = content.model_copy(
                update={
                    "uri": content.uri or resource_registry.uri,
                    "name": content.name
                    or resource_registry.extra.get("name")
                    or resource_registry.metadata.name,
                    "title": content.title
                    or resource_registry.extra.get("title")
                    or resource_registry.metadata.title,
                    "annotations": content.annotations
                    or resource_registry.extra.get("annotations"),
                }
            )

            content_schema_list.append(updated_content)

        content_schema = ContentSchema(contents=content_schema_list)
        content_schema = self._build_non_none_dict(content_schema)
        return content_schema
