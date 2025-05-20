# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import Any

from pydantic import BaseModel

PYDANTIC_TYPES_MAPPING = {
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "string": "str",
}


class ConfigurableParametersRESTViews:
    """
    Base class for converting configurable parameters to REST views.

    This class provides methods to transform Pydantic models and their fields
    into REST-compatible dictionary representations.
    """

    @staticmethod
    def _parameter_to_rest(key: str, value: int | float | str | bool, json_schema: dict) -> dict[str, Any]:
        """
        Convert a single parameter to its REST representation.

        :param key: The parameter name/key
        :param value: The parameter value (int, float, string, or boolean)
        :param json_schema: The JSON schema for the parameter from the Pydantic model
        :return: Dictionary containing the REST representation of the parameter
        """
        rest_view = {
            "key": key,
            "name": json_schema.get("title"),
            "description": json_schema.get("description"),
            "value": value,
            "default_value": json_schema.get("default"),
        }
        # optional parameter may contain `'anyOf': [{'exclusiveMinimum': 0, 'type': 'integer'}, {'type': 'null'}]`
        type_any_of = json_schema.get("anyOf", [{}])[0]
        rest_view["type"] = PYDANTIC_TYPES_MAPPING.get(json_schema.get("type", type_any_of.get("type")))
        if rest_view["type"] in ["int", "float"]:
            rest_view["min_value"] = json_schema.get("minimum", type_any_of.get("exclusiveMinimum"))
            rest_view["max_value"] = json_schema.get("maximum", type_any_of.get("exclusiveMaximum"))
        return rest_view

    @classmethod
    def configurable_parameters_to_rest(cls, configurable_parameters: BaseModel) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Convert a Pydantic model of configurable parameters to its REST representation.

        This method processes a Pydantic model containing configuration parameters and transforms it
        into a REST view. It handles both simple fields and nested models:

        - Simple fields (int, float, str, bool) are converted to a list of dictionaries with metadata
            including key, name, description, value, type, and constraints
        - Nested Pydantic models are processed recursively and maintained as nested structures

        The return format depends on the content:
        - If only simple parameters exist: returns a list of parameter dictionaries
        - If only nested models exist: returns a dictionary mapping nested model names to their contents
        - If both exist: returns a list containing parameter dictionaries and nested model dictionary

        :param configurable_parameters: Pydantic model containing configurable parameters
        :return: REST representation as either a dictionary of nested models,
            a list of parameter dictionaries, or a combined list of both
        """
        nested_params: dict[str, Any] = {}
        list_params: list[dict[str, Any]] = []

        for field_name in configurable_parameters.model_fields:
            field = getattr(configurable_parameters, field_name)
            if isinstance(field, BaseModel):
                # If the field is a nested Pydantic model, process it recursively
                nested_params[field_name] = cls.configurable_parameters_to_rest(field)
            else:
                # If the field is a simple type, convert directly to REST view
                json_model = configurable_parameters.model_json_schema()
                list_params.append(
                    cls._parameter_to_rest(
                        key=field_name,
                        value=field,
                        json_schema=json_model["properties"][field_name],
                    )
                )

        # Return combined or individual results based on content
        if nested_params and list_params:
            return list_params + [nested_params]
        return list_params or nested_params
