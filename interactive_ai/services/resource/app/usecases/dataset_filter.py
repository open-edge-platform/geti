"""This file is responsible for translating a query in JSON format to a dataclass and validating it"""

# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
import datetime
import re
import typing
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from bson import ObjectId

from communication.exceptions import InvalidFilterException

from geti_types import MediaType


class DatasetFilterOperator(Enum):
    """
    This enum contains all possible mongodb operators that can be used to query the db.
    """

    GREATER = "$gt"
    LESS = "$lt"
    GREATER_OR_EQUAL = "$gte"
    LESS_OR_EQUAL = "$lte"
    EQUAL = "$eq"
    NOT_EQUAL = "$ne"
    IN = "$in"
    NOT_IN = "$nin"
    CONTAINS = "$regex"


EQUALITY_OPERATORS = [DatasetFilterOperator.EQUAL, DatasetFilterOperator.NOT_EQUAL]
STRICTLY_GREATER_OR_LESSER_OPERATORS = [
    DatasetFilterOperator.GREATER,
    DatasetFilterOperator.LESS,
]
GREATER_LESSER_EQUAL_OPERATORS = [
    DatasetFilterOperator.GREATER_OR_EQUAL,
    DatasetFilterOperator.LESS_OR_EQUAL,
]
ALL_GREATER_LESSER_OPERATORS = STRICTLY_GREATER_OR_LESSER_OPERATORS + GREATER_LESSER_EQUAL_OPERATORS
EXISTENCE_OPERATORS = [DatasetFilterOperator.IN, DatasetFilterOperator.NOT_IN]

MAXIMUM_FILTER_STRING_LENGTH = 255


class DatabaseItemType(Enum):
    """
    This enum contains possible types of items in the database.
    """

    DEFAULT = auto()
    OBJECT_ID = auto()  # Mongo ID
    ISODATE = auto()  # Mongo Datetime


class FilterInfo(typing.NamedTuple):
    """
    This named tuple contains info about the filter such as the exact name of the column
    in the database, the allowed operators and the type of the filter value and the
    database item type.
    """

    column_name: str
    allowed_operators: list[DatasetFilterOperator]
    allowed_type: type
    database_type: DatabaseItemType = DatabaseItemType.DEFAULT
    nullable: bool = False


class FilterField(Enum):
    def __new__(cls, *args, **kwargs):  # noqa: ARG004
        obj = object.__new__(cls)
        obj._value_ = args[1].column_name  # FilterInfo is expected as second argument
        return obj

    def __init__(
        self,
        value: int,  # noqa: ARG002
        filter_info: FilterInfo,
    ) -> None:
        """
        :param value: Unique integer for .value property of Enum (auto() does not work)
        :param filter_info: NamedTuple containing information about the filter

        """
        self.column_name = filter_info.column_name
        self.allowed_operators = filter_info.allowed_operators
        self.allowed_type = filter_info.allowed_type
        self.database_type = filter_info.database_type
        self.nullable = filter_info.nullable

    def validate_operator(self, operator: DatasetFilterOperator) -> None:
        """
        Validates that the combination of operator and field is allowed
        """
        if operator not in self.allowed_operators:
            raise InvalidFilterException(
                f"Operator {operator.value} is not allowed for {self.name}. "
                f"Allowed operators are {[operator.name for operator in self.allowed_operators]}"
            )

    def validate_value(self, value: Any, operator: DatasetFilterOperator) -> None:
        """
        Validates that the combination of value and field is allowed
        """
        # In case an existence operator is used a list of values should be checked
        if value is None and self.nullable:
            return
        if isinstance(value, Sequence) and not isinstance(value, str):
            if operator not in EXISTENCE_OPERATORS:
                raise InvalidFilterException(
                    f"Expected a single value for operator '{operator.value}', but got a sequence instead: '{value}'."
                )
            for item in value:
                try:
                    self.allowed_type(item)
                except ValueError:
                    raise InvalidFilterException(f"Value for field {self.name} must be of type {self.allowed_type}")
        else:
            if operator in EXISTENCE_OPERATORS:
                raise InvalidFilterException(
                    f"Expected a sequence for operator '{operator.value}', but got a single value instead: '{value}'."
                )
            try:
                self.allowed_type(value)
            except ValueError:
                raise InvalidFilterException(f"Value for field {self.name} must be of type {self.allowed_type}")
        # Mongo only allows max int of 64 bits
        if self.allowed_type is int and (value > 2**63 - 1 or value < -(2**63)):
            raise InvalidFilterException(f"Value for field {self.name} is larger than 64 bits. This is not allowed.")
        if self.allowed_type is str and len(value) > MAXIMUM_FILTER_STRING_LENGTH:
            raise InvalidFilterException(
                f"String length for field {self.name} is longer than {MAXIMUM_FILTER_STRING_LENGTH}. This is not "
                f"allowed."
            )


class DatasetFilterField(FilterField):
    """
    This enum contains all possible columns in mongo that can be queried along with the
    allowed operators that can be used on the column
    """

    MEDIA_UPLOAD_DATE = (
        1,
        FilterInfo(
            column_name="upload_date",
            allowed_operators=STRICTLY_GREATER_OR_LESSER_OPERATORS,
            allowed_type=str,
            database_type=DatabaseItemType.ISODATE,
        ),
    )
    MEDIA_HEIGHT = (
        2,
        FilterInfo(
            column_name="media_height",
            allowed_operators=ALL_GREATER_LESSER_OPERATORS + EQUALITY_OPERATORS,
            allowed_type=int,
        ),
    )
    MEDIA_WIDTH = (
        3,
        FilterInfo(
            column_name="media_width",
            allowed_operators=ALL_GREATER_LESSER_OPERATORS + EQUALITY_OPERATORS,
            allowed_type=int,
        ),
    )
    MEDIA_NAME = (
        4,
        FilterInfo(
            column_name="media_name",
            allowed_operators=[*EQUALITY_OPERATORS, DatasetFilterOperator.CONTAINS],
            allowed_type=str,
        ),
    )
    LABEL_ID = (
        5,
        FilterInfo(
            column_name="label_ids",
            allowed_operators=EQUALITY_OPERATORS + EXISTENCE_OPERATORS,
            allowed_type=str,
            database_type=DatabaseItemType.OBJECT_ID,
        ),
    )
    ANNOTATION_CREATION_DATE = (
        6,
        FilterInfo(
            column_name="creation_date",
            allowed_operators=STRICTLY_GREATER_OR_LESSER_OPERATORS,
            allowed_type=str,
            database_type=DatabaseItemType.ISODATE,
        ),
    )
    ANNOTATION_SCENE_STATE = (
        7,
        FilterInfo(
            column_name="media_annotation_state",
            allowed_operators=[DatasetFilterOperator.EQUAL, DatasetFilterOperator.IN],
            allowed_type=str,
        ),
    )
    SHAPE_TYPE = (
        8,
        FilterInfo(
            column_name="annotations.shape.type",
            allowed_operators=EQUALITY_OPERATORS + EXISTENCE_OPERATORS,
            allowed_type=str,
        ),
    )
    SHAPE_AREA_PERCENTAGE = (
        9,
        FilterInfo(
            column_name="annotations.shape.area_percentage",
            allowed_operators=ALL_GREATER_LESSER_OPERATORS + EQUALITY_OPERATORS,
            allowed_type=float,
        ),
    )
    SHAPE_AREA_PIXEL = (
        10,
        FilterInfo(
            column_name="annotations.shape.area_pixel",
            allowed_operators=ALL_GREATER_LESSER_OPERATORS + EQUALITY_OPERATORS,
            allowed_type=int,
        ),
    )
    USER_NAME = (
        11,
        FilterInfo(
            column_name="user_name",
            allowed_operators=EQUALITY_OPERATORS + EXISTENCE_OPERATORS,
            allowed_type=str,
        ),
    )
    SUBSET = (
        12,
        FilterInfo(
            column_name="subset",
            allowed_operators=[DatasetFilterOperator.EQUAL],
            allowed_type=str,
        ),
    )
    MEDIA_TYPE = (
        13,
        FilterInfo(
            column_name="media_identifier.type",
            allowed_operators=[DatasetFilterOperator.EQUAL],
            allowed_type=str,
        ),
    )
    MEDIA_SIZE = (
        14,
        FilterInfo(
            column_name="size",
            allowed_operators=ALL_GREATER_LESSER_OPERATORS + EQUALITY_OPERATORS,
            allowed_type=int,
        ),
    )
    VIDEO_DURATION = (
        15,
        FilterInfo(
            column_name="duration",
            allowed_operators=ALL_GREATER_LESSER_OPERATORS + EQUALITY_OPERATORS,
            allowed_type=int,
        ),
    )
    VIDEO_FRAME_RATE = (
        16,
        FilterInfo(
            column_name="frame_rate",
            allowed_operators=ALL_GREATER_LESSER_OPERATORS + EQUALITY_OPERATORS,
            allowed_type=float,
        ),
    )
    VIDEO_FRAME_COUNT = (
        17,
        FilterInfo(
            column_name="frame_count",
            allowed_operators=ALL_GREATER_LESSER_OPERATORS + EQUALITY_OPERATORS,
            allowed_type=int,
        ),
    )


class MediaScoreFilterField(FilterField):
    """
    Enum defining the possible media score field types
    """

    LABEL_ID = (
        1,
        FilterInfo(
            column_name="label_id",
            allowed_operators=[DatasetFilterOperator.EQUAL],
            allowed_type=str,
            database_type=DatabaseItemType.OBJECT_ID,
            nullable=True,
        ),
    )
    SCORE = (
        2,
        FilterInfo(
            column_name="score",
            allowed_operators=ALL_GREATER_LESSER_OPERATORS,
            allowed_type=float,
        ),
    )


class DatasetFilterCondition(Enum):
    """
    This enum contains conditions that can be applied to a group of DatasetFilterRule's
    """

    AND = "$and"


class DatasetFilterSortDirection(Enum):
    """
    This enum contains sort directions to use in the filter
    """

    ASC = 1
    DSC = -1


@dataclass(frozen=True)
class DatasetFilterRule:
    """
    This dataclass defines one filter rule that is a part of a DatasetFilterRuleGroup
    """

    field: FilterField
    operator: DatasetFilterOperator
    value: Any

    @classmethod
    def from_dict(cls, rule: dict, is_media_score_filter: bool = False) -> "DatasetFilterRule":
        """
        Generate a DatasetFilterRule object from a dictionary.

        :param rule: A dictionary containing the json rule
        :param is_media_score_filter: Whether the dataset filter is a media score filter
        :return: A DatasetFilterRule object
        """
        field_value = get_and_validate_key(dictionary=rule, key="field")
        if is_media_score_filter:
            field: FilterField = get_and_validate_enum(enum=MediaScoreFilterField, key=field_value)
        else:
            field: FilterField = get_and_validate_enum(  # type: ignore[no-redef]
                enum=DatasetFilterField, key=field_value
            )

        operator_str = get_and_validate_key(dictionary=rule, key="operator")
        operator: DatasetFilterOperator = get_and_validate_enum(enum=DatasetFilterOperator, key=operator_str)

        value = get_and_validate_key(dictionary=rule, key="value")
        field.validate_operator(operator=operator)
        field.validate_value(value=value, operator=operator)
        return cls(
            field=field,
            operator=operator,
            value=value,
        )


@dataclass(frozen=True)
class DatasetFilterRuleGroup:
    """
    This dataclass contains a list with rules along with the condition that should be
    applied to the group of rules.
    """

    group_of_rules: list[DatasetFilterRule]
    condition: DatasetFilterCondition = DatasetFilterCondition.AND

    @classmethod
    def from_dict(cls, query: dict, is_media_score_filter: bool = False) -> "DatasetFilterRuleGroup":
        """
        Generate a DatasetFilterRuleGroup object from a dictionary.

        :param query: A dictionary containing the json query
        :param is_media_score_filter: Whether the dataset filter is a media score filter
        :return: A DatasetFilterRuleGroup object
        """
        rules: list[dict] = get_and_validate_key(query, "rules")
        group_of_rules = [
            DatasetFilterRule.from_dict(rule, is_media_score_filter=is_media_score_filter) for rule in rules
        ]
        return cls(group_of_rules=group_of_rules)

    def unique_fields(self) -> list[FilterField]:
        """
        Returns all the unique DatasetFilterFields that are in a DatasetFilterRuleGroup.
        This method can be used to determine what aggregation needs to be done on the
        repos to retrieve all desired items
        """
        fields = []
        for rule in self.group_of_rules:
            fields.append(rule.field)
        return list(set(fields))

    def generate_match_query(self) -> dict:
        """
        Recursively resolves all the filters and creates a query that can be used to
        match against in mongodb
        """
        query: dict = {self.condition.value: []}
        for rule in self.group_of_rules:
            value = self._get_value_for_database_type(rule=rule)
            if rule.operator == DatasetFilterOperator.CONTAINS:
                filter_value = {
                    rule.field.value: {
                        rule.operator.value: re.escape(value),
                        "$options": "i",  # i option is case insensitivity
                    }
                }
            elif rule.field == DatasetFilterField.SUBSET:
                filter_value = {rule.field.value: {rule.operator.value: value.upper()}}
            elif rule.field == DatasetFilterField.MEDIA_TYPE:
                if value.lower() == MediaType.VIDEO.value:
                    # For MediaType.VIDEO we have to filter on MediaType.VIDEO_FRAME as well to ensure
                    # any annotation scene made on the video are filtered correctly.
                    filter_value = {rule.field.value: {"$in": ["video", "video_frame"]}}
                else:
                    filter_value = {
                        rule.field.value: {
                            rule.operator.value: value.lower(),
                            "$exists": True,
                        }
                    }
            else:
                filter_value = {rule.field.value: {rule.operator.value: value, "$exists": True}}

            query[self.condition.value].append(filter_value)
        if len(query[self.condition.value]) > 0:
            return query
        return {}

    @staticmethod
    def _get_value_for_database_type(rule: DatasetFilterRule) -> Any:
        """
        Converts the value of a DatasetFilterRule to the correct type in the database.

        :param rule: Rule to convert value of to correct type
        :return:
        """
        value: Any
        if rule.field.nullable and rule.value is None:
            value = None
        elif rule.field.database_type == DatabaseItemType.ISODATE:
            if rule.operator in EXISTENCE_OPERATORS:
                value = [datetime.datetime.fromisoformat(value) for value in rule.value]
            else:
                value = datetime.datetime.fromisoformat(rule.value)  # type:ignore[assignment]
        elif rule.field.database_type == DatabaseItemType.OBJECT_ID:
            if rule.operator in EXISTENCE_OPERATORS:
                value = [ObjectId(value) for value in rule.value]
            else:
                value = ObjectId(rule.value)
        else:
            value = rule.value
        return value


@dataclass
class DatasetFilter:
    """
    This class can be used to translate and validate a JSON query and store it in an
    object.
    """

    limit: int
    skip: int
    _ruleset: DatasetFilterRuleGroup
    sort_by: FilterField
    sort_direction: DatasetFilterSortDirection
    id_: str

    @classmethod
    def from_dict(
        cls,
        query: dict,
        limit: int,
        skip: int = 0,
        sort_by: FilterField = DatasetFilterField.MEDIA_NAME,
        sort_direction: DatasetFilterSortDirection = DatasetFilterSortDirection.ASC,
    ) -> "DatasetFilter":
        """
        Generate a DatasetFilter object from a dictionary.

        :param query: dictionary with rules to filter with
        :param limit: amount of items to limit per page for pagination
        :param skip: How many items to skip ahead of. Used for pagination
        :param sort_by: Field to sort on
        :param sort_direction: Direction to sort the sort_by field
        :return: DatasetFilter
        """
        if query == {}:
            return NullDatasetFilter(
                limit=limit,
                skip=skip,
                _ruleset=DatasetFilterRuleGroup(group_of_rules=[]),
                sort_by=sort_by,
                sort_direction=sort_direction,
                id_=uuid.uuid4().hex[:16],
            )

        is_media_score_filter = isinstance(sort_by, MediaScoreFilterField)
        rule_set = DatasetFilterRuleGroup.from_dict(query, is_media_score_filter=is_media_score_filter)
        if len(rule_set.group_of_rules) == 0:
            raise InvalidFilterException(
                'Can not create filter with a condition but no rules. Pass "{}" if '
                "you want a filter that retrieves all items."
            )
        return cls(
            limit=limit,
            skip=skip,
            _ruleset=rule_set,
            sort_by=sort_by,
            sort_direction=sort_direction,
            id_=uuid.uuid4().hex[:16],
        )

    def unique_fields(self) -> list[FilterField]:
        """
        Returns all the unique DatasetFilterFields that are in the group_of_rules of the
        ruleset. This method can be used to determine what aggregation needs to be done
        on the repos to retrieve all desired items
        """
        return self._ruleset.unique_fields()

    def generate_match_query(self) -> dict:
        """
        Recursively resolves all the filters and creates a query that can be used to
        match against in mongodb
        """
        return {"$match": self._ruleset.generate_match_query()}

    def generate_sort_query(self) -> dict:
        """
        Creates a query that can be used to sort results based on dataset filter sort_by and sort_direction
        :return: sort query
        """
        # Note: the secondary sort key '_id' ensures a stable order when the primary column has duplicate values.
        # For more details: https://www.mongodb.com/docs/manual/reference/operator/aggregation/sort/#sort-consistency
        return {
            "$sort": {
                self.sort_by.column_name: self.sort_direction.value,
                "_id": self.sort_direction.value,
            }
        }

    def generate_pagination_query(self, group_stage: dict | None = None) -> dict:
        """
        Creates a query that can be used to paginate results based on dataset filter skip and limit

        :param group_stage: dict containing MongoDB group stage in case video frames should be grouped by video
        :return: pagination query
        """
        pagination_pipeline = [
            self.generate_sort_query(),
            {"$skip": self.skip},
            {"$limit": self.limit},
        ]
        if group_stage is not None:
            pagination_pipeline.insert(0, group_stage)

        return {
            "$facet": {
                "paginated_results": pagination_pipeline,
                "image_count": [
                    {"$match": {"media_identifier.type": MediaType.IMAGE.value}},
                    {"$count": "count"},
                ],
                "video_count": [
                    {
                        "$match": {
                            "media_identifier.type": {
                                "$in": [
                                    MediaType.VIDEO.value,
                                    MediaType.VIDEO_FRAME.value,
                                ]
                            }
                        }
                    },
                    {"$group": {"_id": "$media_identifier.media_id"}},
                    {"$count": "count"},
                ],
                "video_frame_count": [
                    {
                        "$match": {
                            "media_identifier.type": {
                                "$in": [
                                    MediaType.VIDEO.value,
                                    MediaType.VIDEO_FRAME.value,
                                ]
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": 1,
                            "count": {
                                "$sum": {"$ifNull": ["$unannotated_frames", 1]},
                            },
                        }
                    },
                ],
            }
        }


@dataclass
class NullDatasetFilter(DatasetFilter):
    """
    This NullDatasetFilter represents an empty filter to apply in the database. This
    means all items in the db will be returned by it.
    """

    def generate_match_query(self) -> dict:
        return {"$match": {}}


def get_and_validate_key(dictionary: dict, key: str) -> Any:
    """
    Gets and returns a value from a dictionary by key safely. If the key is not
    available an InvalidFilterException is raised.
    """
    try:
        value = dictionary[key]
    except KeyError:
        raise InvalidFilterException(f"Invalid filter provided. Missing key {key} in dictionary {dictionary}")
    return value


@typing.no_type_check
def get_and_validate_enum(
    enum: (
        type[DatasetFilterOperator]
        | type[DatasetFilterField]
        | type[DatasetFilterCondition]
        | type[DatasetFilterSortDirection]
        | type[MediaScoreFilterField]
    ),
    key: str,
) -> (
    DatasetFilterOperator
    | DatasetFilterField
    | MediaScoreFilterField
    | DatasetFilterCondition
    | DatasetFilterSortDirection
):
    """
    Gets and returns a value from an enum by key safely. If the key is not
    available an InvalidFilterException is raised.
    """
    try:
        value = enum[key.upper()]
    except KeyError:
        raise InvalidFilterException(
            f"Invalid filter provided. {key} is not a valid value for enum "
            f"{enum.__name__}. Please choose one of {[e.name for e in enum]}"
        )
    return value
