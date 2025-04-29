# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from bson import ObjectId

from geti_fastapi_tools.exceptions import BadRequestException, InvalidIDException


class RestValidationHelpers:
    @staticmethod
    def validate_objectid_field(args: dict, name: str) -> None:
        """
        Validate ObjectID-like field in args dict with given name
         - check that id is provided
         - check that provided value is valid for id creation as ObjectId

        :param args: dict of query args
        :param name: name of the field
        :raises BadRequestException: if field does not exist or id is invalid
        """
        value = args.get(name)
        if value is None:
            raise BadRequestException(f"Missing required query parameter '{name}'")
        if not ObjectId.is_valid(value):
            raise InvalidIDException(id_name=name, invalid_id=value)

    @staticmethod
    def validate_objectid_list_field(args: dict, name: str, single_item: bool = False) -> None:
        """
        Validate list of ObjectID-like fields in args dict with given name
        - check that list of ids is provided
        - check that type of the value is indeed a list
        - check that list has at least one item
        - check that each item in list is valid for id creation as ObjectId

        :param args: dict of query args
        :param name: name of the field
        :param single_item: if True, check that only one item is present in list
        :raises BadRequestException: if field does not exist or if the value is not a list of valid ids
        """
        value = args.get(name)
        if value is None:
            raise BadRequestException(f"Missing required query parameter '{name}'")
        if not isinstance(value, list):
            raise BadRequestException(f"Parameter '{name}' should be a list")
        if single_item and len(value) != 1:
            raise BadRequestException(f"List parameter '{name}' should have exactly one item in current version")
        if len(value) == 0:
            raise BadRequestException(f"List parameter '{name}' should have at least one item")
        for item in value:
            if not ObjectId.is_valid(item):
                raise InvalidIDException(id_name=name, invalid_id=item)
