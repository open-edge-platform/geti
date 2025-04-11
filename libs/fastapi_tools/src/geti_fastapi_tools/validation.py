import os
from copy import deepcopy
from pathlib import Path

import yaml

MAX_STRING_LENGTH = 1000
MIN_STRING_LENGTH = 1


class RestApiValidator:
    """
    A class to validate REST API schemas by loading and resolving references in YAML files.

    This class provides methods to load a schema file, convert it to a dictionary, and
    recursively resolve any references within the schema. It ensures that all string
    fields have a maximum and minimum length and removes any example fields from the
    schema.
    """

    @classmethod
    def load_schema_file_as_dict(cls, schema_absolute_path: str) -> dict:
        """
        Load a schema file and convert it to a dict, using a helper function to
        recursively resolve references in the schema.

        :param schema_absolute_path: absolute path of the schema file
        """
        with open(schema_absolute_path) as yaml_file:
            schema = yaml.safe_load(yaml_file)
        schema_dict = cls.__resolve_references_in_schema_dict(schema, os.path.dirname(schema_absolute_path))
        schema_dict["additionalProperties"] = False
        return schema_dict

    @classmethod
    def __resolve_references_in_schema_dict(cls, schema_dict: dict, current_dir: str):
        """
        Recursively resolves all "$ref" values with dictionaries from the referenced
        loaded file.

        Step 1: Iterate through all the items and recursively resolve all lower dicts
            and lists
        Step 2: Iterate through a copy of the dictionary and find occurrences of
            "$ref". For every $ref, open the relevant schema file and resolve all
            references in it. Then, add the contents of the $ref to schema_dict.

        Additionally, for every string in the schema, add a max length.

        :param schema_dict: schema dictionary to resolve references for
        :param current_dir: directory of the yaml file currently being resolved
        return: updated schema_dict with all references resolved
        """
        new_schema_dict = {}
        for key, value in schema_dict.items():
            if key == "$ref":
                yaml_path = cls.__resolve_absolute_path(current_dir, value)
                with open(yaml_path) as yaml_file:
                    schema = yaml.safe_load(yaml_file)
                    yaml_file_contents = cls.__resolve_references_in_item(schema, os.path.dirname(yaml_path))
                    new_schema_dict.update(yaml_file_contents)
            elif key == "type" and value == "string":
                new_schema_dict["type"] = "string"
                new_schema_dict["maxLength"] = schema_dict.get("maxLength", MAX_STRING_LENGTH)
                new_schema_dict["minLength"] = schema_dict.get("minLength", MIN_STRING_LENGTH)
            else:
                new_schema_dict[key] = cls.__resolve_references_in_item(value, current_dir)
        new_schema_dict.pop("examples", None)
        new_schema_dict.pop("example", None)
        return new_schema_dict

    @classmethod
    def __resolve_references_in_schema_list(cls, schema_list, current_dir):  # noqa: ANN001
        """
        Iterate through a list and resolve all elements within it
        """
        resolved_list = deepcopy(schema_list)
        for list_index, item in enumerate(schema_list):
            resolved_list[list_index] = cls.__resolve_references_in_item(item, current_dir)
        return resolved_list

    @classmethod
    def __resolve_references_in_item(cls, item_to_resolve, current_dir):  # noqa: ANN001
        """
        Recursively resolve references in a list or dictionary by calling the proper
        function that loops through it
        """
        if isinstance(item_to_resolve, dict) and len(item_to_resolve) > 0:
            resolved_item = cls.__resolve_references_in_schema_dict(item_to_resolve, current_dir)
        elif isinstance(item_to_resolve, list) and len(item_to_resolve) > 0:
            resolved_item = cls.__resolve_references_in_schema_list(item_to_resolve, current_dir)
        else:
            resolved_item = item_to_resolve
        return resolved_item

    @staticmethod
    def __resolve_absolute_path(current_dir: str, dict_value: str) -> str:
        """
        For a $ref found in a file in current_dir, determine the path of the
        referenced file.

        :param current_dir: path to the file where the $ref is
        :param dict_value: path relative to the file where the $ref is, as specified
            in the file.
        return: path to the referenced file, only specifying everything after
            microservices/communication/schemas
        """
        yaml_path = os.path.join(current_dir, dict_value)
        return str(Path(yaml_path).resolve())
