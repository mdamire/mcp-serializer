from typing import Optional
from .schema import (
    ArgumentSchema,
    PromptDefinitionSchema,
    PromptsListSchema,
    PromptResultSchema,
)
from ..base.assembler import FeatureSchemaAssembler
from .result import PromptsResult
from ..base.pagination import Pagination
from ..base.definitions import FunctionMetadata


class PromptsSchemaAssembler(FeatureSchemaAssembler):
    def __init__(self):
        self.prompts_list = []

    def add_registry(self, registry):
        from .container import PromptRegistry, ResultRegistry

        if isinstance(registry, PromptRegistry):
            metadata = registry.metadata
            arguments_schema = self._create_arguments_schema(metadata)

            definition_schema = PromptDefinitionSchema(
                name=registry.extra.get("name") or metadata.name,
                title=registry.extra.get("title") or metadata.title,
                description=registry.extra.get("description") or metadata.description,
                arguments=arguments_schema,
            )
        elif isinstance(registry, ResultRegistry):
            definition_schema = PromptDefinitionSchema(
                name=registry.name,
                title=registry.extra.get("title"),
                description=registry.extra.get("description"),
                arguments=None,
            )
        else:
            raise ValueError(f"Unsupported registry type: {type(registry)}")

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
            arg_schema = ArgumentSchema(
                name=arg.name,
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

    def _check_tuple_result(self, result) -> bool:
        return (
            (isinstance(result, list) or isinstance(result, tuple))
            and len(result) == 2
            and isinstance(result[0], str)
            and PromptsResult.Roles.has_value(result[1])
        )

    def process_result(self, result: PromptsResult, registry):
        """Process the result from prompt function calls."""
        from .container import PromptRegistry

        description = registry.extra.get("description")
        if isinstance(registry, PromptRegistry) and not description:
            description = registry.metadata.description

        if isinstance(result, str):
            prompts = PromptsResult()
            prompts.add_text(result)
            messages = prompts.messages
        elif self._check_tuple_result(result):
            text, role = result
            prompts = PromptsResult()
            prompts.add_text(text, role=role)
            messages = prompts.messages
        elif isinstance(result, PromptsResult):
            messages = result.messages
            description = result.description or description
        else:
            raise self.UnsupportedResultTypeError(
                f"Unsupported result type: {type(result)}"
            )

        result_schema = PromptResultSchema(
            description=description,
            messages=messages,
        )
        return self._build_non_none_dict(result_schema)
