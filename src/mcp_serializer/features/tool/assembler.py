from typing import Optional
from pydantic import BaseModel
from pydantic_core import PydanticUndefined
import inspect
from ..base.pagination import Pagination
from .schema import ToolsDefinitionSchema, ToolsListSchema, ResultSchema, TextContent
from ..base.assembler import FeatureSchemaAssembler
from ..base.schema import JsonSchema
from .result import ToolsResult
from ..base.definitions import FunctionMetadata


class ToolsSchemaAssembler(FeatureSchemaAssembler):
    def __init__(self):
        super().__init__()
        self.tools_list = []

    def add_tool_registry(self, registry):
        metadata = registry.metadata

        # Create input schema from function arguments
        input_schema = self._create_input_schema(metadata)

        # Create output schema if return type is Pydantic BaseModel
        output_schema = self._create_output_schema(metadata)

        # Build definition schema
        definition_schema = ToolsDefinitionSchema(
            name=registry.extra.get("name") or metadata.name,
            title=registry.extra.get("title") or metadata.title,
            description=registry.extra.get("description") or metadata.description,
            inputSchema=input_schema,
            outputSchema=output_schema,
            annotations=registry.extra.get("annotations"),
        )

        # Convert to dict and add to tools list
        self._append_sorted_list(
            self.tools_list, self._build_non_none_dict(definition_schema), "name"
        )
        return definition_schema

    def _create_input_schema(self, metadata):
        if not metadata.arguments:
            return None

        input_schema = JsonSchema()

        for arg in metadata.arguments:
            has_default = arg.default is not FunctionMetadata.empty
            input_schema.add_property(
                name=arg.name,
                type_hint=arg.type_hint,
                description=arg.description,
                required=arg.required,
                default=arg.default if has_default else None,
                has_default=has_default,
            )

        return input_schema

    def _create_output_schema(self, metadata):
        """Create output schema from return type if it's a Pydantic BaseModel.

        Example:
            class WeatherResponse(BaseModel):
                temperature: float = Field(description="Temperature in celsius")
                conditions: str = Field(description="Weather conditions description")
        """
        if not metadata.return_type:
            return None

        # Check if return type is a Pydantic BaseModel
        if inspect.isclass(metadata.return_type) and issubclass(
            metadata.return_type, BaseModel
        ):
            output_schema = JsonSchema()

            # Get fields from Pydantic model
            if hasattr(metadata.return_type, "model_fields"):
                for field_name, field_info in metadata.return_type.model_fields.items():
                    has_default = field_info.default is not PydanticUndefined
                    output_schema.add_property(
                        name=field_name,
                        type_hint=field_info.annotation,
                        description=field_info.description,
                        required=field_info.is_required(),
                        default=field_info.default if has_default else None,
                        has_default=has_default,
                    )

            return output_schema

        return None

    def build_list_result_schema(
        self, page_size: int = 10, cursor: Optional[str] = None
    ):
        pagination = Pagination(page_size)
        paginated_tools, next_cursor = pagination.paginate(self.tools_list, cursor)
        return ToolsListSchema(
            tools=paginated_tools, nextCursor=next_cursor
        ).model_dump()

    def process_result(self, result):
        result_schema = ResultSchema()
        if isinstance(result, ToolsResult):
            if result.content_list:
                result_schema.content = [
                    item.model_dump() if hasattr(item, "model_dump") else item
                    for item in result.content_list
                ]
            if result.structured_content:
                result_schema.structuredContent = result.structured_content
            if result.is_error:
                result_schema.isError = result.is_error
        elif isinstance(result, BaseModel):
            result_schema.structuredContent = result.model_dump()
        elif isinstance(result, dict):
            result_schema.structuredContent = result
        elif isinstance(result, str):
            result_schema.content = [TextContent(text=result).model_dump()]
        else:
            raise self.UnsupportedResultTypeError(type(result))

        return self._build_non_none_dict(result_schema)
