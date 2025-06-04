# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import Any

from pydantic import BaseModel

PYDANTIC_BASE_TYPES_MAPPING = {
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "string": "str",
}
PYDANTIC_ANY_OF = "anyOf"


class ConfigurableParametersRESTViews:
    """
    Base class for converting configurable parameters to REST views.

    This class provides methods to transform Pydantic models and their fields
    into REST-compatible dictionary representations.
    """

    @staticmethod
    def _parameter_to_rest(key: str, rest_type: str, value: float | str | bool, json_schema: dict) -> dict[str, Any]:
        """
        Convert a single parameter to its REST representation.

        :param key: The parameter name/key
        :param rest_type: The parameter type (int, float, string, or boolean)
        :param value: The parameter value (int, float, string, or boolean)
        :param json_schema: The JSON schema for the parameter from the Pydantic model
        :return: Dictionary containing the REST representation of the parameter
        """
        default = json_schema.get("default")
        default_value = default if default is not None else json_schema.get("default_value")
        rest_view = {
            "key": key,
            "name": json_schema.get("title"),
            "type": rest_type,
            "description": json_schema.get("description"),
            "value": value,
            "default_value": default_value,
        }
        # optional parameter may contain `'anyOf': [{'exclusiveMinimum': 0, 'type': 'integer'}, {'type': 'null'}]`
        type_any_of = json_schema.get(PYDANTIC_ANY_OF, [{}])[0]
        rest_view["type"] = PYDANTIC_BASE_TYPES_MAPPING.get(json_schema.get("type", type_any_of.get("type")))
        if rest_view["type"] in ["int", "float"]:
            # min/max values can be contained in "minimum", "exclusiveMinimum" or 'anyOf.*'
            rest_view["min_value"] = json_schema.get(
                "minimum",
                json_schema.get("exclusiveMinimum", type_any_of.get("minimum", type_any_of.get("exclusiveMinimum"))),
            )
            rest_view["max_value"] = json_schema.get(
                "maximum",
                json_schema.get("exclusiveMaximum", type_any_of.get("maximum", type_any_of.get("exclusiveMaximum"))),
            )
        return rest_view

    @classmethod
    def configurable_parameters_to_rest(
        cls, configurable_parameters: BaseModel
    ) -> dict[str, Any] | list[dict[str, Any]]:
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

        json_model = configurable_parameters.model_json_schema()
        for field_name in configurable_parameters.model_fields:
            field = getattr(configurable_parameters, field_name)

            schema = json_model["properties"][field_name]
            # optional parameter may contain `'anyOf': [{'exclusiveMinimum': 0, 'type': 'integer'}, {'type': 'null'}]`
            type_any_of = schema.get(PYDANTIC_ANY_OF, [{}])[0]
            pydantic_type = schema.get("type", type_any_of.get("type"))

            if field is None:
                # Do not show None values in the REST view. None parameters means they are not supported
                continue

            if pydantic_type in PYDANTIC_BASE_TYPES_MAPPING:
                # If the field is a simple type, convert directly to REST view
                list_params.append(
                    cls._parameter_to_rest(
                        key=field_name,
                        rest_type=PYDANTIC_BASE_TYPES_MAPPING[pydantic_type],
                        value=field,
                        json_schema=schema,
                    )
                )
            else:
                # If the field is a nested Pydantic model, process it recursively
                nested_params[field_name] = cls.configurable_parameters_to_rest(configurable_parameters=field)

        # Return combined or individual results based on content
        if nested_params and list_params:
            return [*list_params, nested_params]
        return list_params or nested_params

    @classmethod
    def configurable_parameters_from_rest(
        cls, configurable_parameters_rest: dict[str, Any] | list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Convert a REST representation back to a dictionary that can be used to create/update a Pydantic model.

        This method performs the reverse operation of configurable_parameters_to_rest:
        - For a list of parameter dictionaries, it extracts the key-value pairs
        - For a dictionary of nested models, it processes each nested model recursively
        - For a mixed list containing both, it handles both types

        :param configurable_parameters_rest: REST representation as a dictionary or list
        :return: Dictionary representation suitable for Pydantic model instantiation
        """
        # If the input is a list (of parameters or mixed)
        if isinstance(configurable_parameters_rest, list):
            result = {}

            for item in configurable_parameters_rest:
                # If this is a parameter entry (has a "key" field)
                if isinstance(item, dict) and "key" in item:
                    key = item["key"]
                    value = item["value"]
                    result[key] = value
                # If it's a dictionary without a "key" field, it must contain nested models
                elif isinstance(item, dict):
                    # Process each nested model recursively and merge with result
                    nested_result = cls.configurable_parameters_from_rest(item)
                    result.update(nested_result)

            return result

        # If the input is a dictionary (of nested models or other fields)
        if isinstance(configurable_parameters_rest, dict):
            result = {}

            for key, value in configurable_parameters_rest.items():
                # If the value is a complex structure, process it recursively
                if isinstance(value, dict | list):
                    result[key] = cls.configurable_parameters_from_rest(value)
                else:
                    # Simple value, keep as is
                    result[key] = value

            return result

        # If it's neither a list nor a dictionary, return it as is
        return configurable_parameters_rest
