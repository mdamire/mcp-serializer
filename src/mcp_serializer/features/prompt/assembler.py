from typing import Optional
from .schema import (
    ArgumentSchema,
    PromptDefinitionSchema,
    PromptsListSchema,
    PromptResultSchema,
)
from ..base.assembler import FeatureSchemaAssembler
from ..base.schema import JsonSchemaTypes
from .result import PromptsResult
from ..base.pagination import Pagination
from ..base.definitions import FunctionMetadata


class PromptsSchemaAssembler(FeatureSchemaAssembler):
    def __init__(self):
        self.prompts_list = []

    def add_registry(self, registry):
        metadata = registry.metadata

        # Create arguments schema from function parameters
        arguments_schema = self._create_arguments_schema(metadata)

        # Build definition schema
        definition_schema = PromptDefinitionSchema(
            name=registry.extra.get("name") or metadata.name,
            title=registry.extra.get("title") or metadata.title,
            description=registry.extra.get("description") or metadata.description,
            arguments=arguments_schema,
        )

        # Convert to dict and add to prompts list
        self._append_sorted_list(
            self.prompts_list, self._build_non_none_dict(definition_schema), "name"
        )
        return definition_schema

    def _create_arguments_schema(self, metadata: FunctionMetadata):
        """Create arguments schema from function arguments."""
        if not metadata.arguments:
            return None

        arguments = []
        for arg in metadata.arguments:
            json_type = JsonSchemaTypes.from_python_type(arg.type_hint)
            arg_schema = ArgumentSchema(
                name=arg.name,
                type=json_type,
                description=arg.description,
                required=arg.required,
            )
            arguments.append(arg_schema.model_dump())

        return arguments

    def build_list_result_schema(
        self, page_size: int = 10, cursor: Optional[str] = None
    ):
        """Build the list result schema for prompts."""
        pagination = Pagination(page_size)
        paginated_prompts, next_cursor = pagination.paginate(self.prompts_list, cursor)
        return PromptsListSchema(
            prompts=paginated_prompts, nextCursor=next_cursor
        ).model_dump()

    def process_result(self, result: PromptsResult, registry):
        """Process the result from prompt function calls."""
        if not isinstance(result, PromptsResult):
            raise self.UnsupportedResultTypeError(
                f"Unsupported result type: {type(result)}"
            )

        result_schema = PromptResultSchema(
            description=registry.extra.get("description")
            or registry.metadata.description,
            messages=result.messages,
        )
        return result_schema.model_dump()
