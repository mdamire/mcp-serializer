from typing import Union
from .pagination import Pagination


class FeatureSchemaAssembler:
    class UnsupportedResultTypeError(Exception):
        def __init__(self, result_type: type):
            self.result_type = result_type
            super().__init__(f"Unsupported result type: {result_type}")

    def _remove_none_from_dict(self, dict_value: dict):
        if not dict_value:
            return None

        if not isinstance(dict_value, dict):
            return dict_value

        new_dict = {}
        for k, v in dict_value.items():
            if isinstance(v, dict):
                v = self._remove_none_from_dict(v)
            elif isinstance(v, list):
                v = [self._remove_none_from_dict(item) for item in v]
            if v is not None:
                new_dict[k] = v

        return new_dict or None

    def _build_non_none_dict(self, schema):
        schema_dict = schema.model_dump() if hasattr(schema, "model_dump") else schema
        updated_dict = self._remove_none_from_dict(schema_dict)
        return updated_dict

    def _append_sorted_list(
        self, target_list: list, obj: Union[dict, object], sort_key_name: str
    ):
        sort_key = (
            lambda x: x[sort_key_name]
            if isinstance(x, dict)
            else getattr(x, sort_key_name)
        )

        target_list.append(obj)
        target_list.sort(key=sort_key)

    def add_definition(self, *args, **kwargs):
        raise NotImplementedError("add_definition")

    def build_list_result_schema(self, *args, **kwargs):
        raise NotImplementedError("build_list_result_schema")
