# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from copy import deepcopy
from functools import cache
from typing import Any, Optional, cast, get_args

from pydantic import BaseModel, ConfigDict, create_model
from pydantic.fields import FieldInfo


@cache  # avoids creating many classes with same name
def partial_model(model: type[BaseModel]) -> type[BaseModel]:
    """
    Creates a new Pydantic model class with all fields made optional.

    This decorator transforms a Pydantic model into a "partial" version where all fields
    are wrapped with Optional and have None as default value. The resulting model
    is particularly useful for:

    - Handling PATCH operations in REST APIs where only some fields need updating
    - Representing partial data structures during validation
    - Supporting incremental configuration changes

    The new model class inherits from the original model, with its name prefixed
    with "Partial" (e.g., "PartialProjectConfiguration").
    """

    @cache
    def make_field_optional(field: FieldInfo) -> tuple[Any, FieldInfo]:
        field.default = None
        field.default_factory = None
        field.annotation = Optional[field.annotation]  # type: ignore[assignment] # noqa: UP007
        return field.annotation, field

    partial_fields = {}
    for field_name, field_info in model.model_fields.items():
        new_field = deepcopy(field_info)
        if not new_field.is_required() and (optional_annotation := get_args(new_field.annotation)):
            # field is already optional, but we still need to make sure that its nested fields are optional too
            field_type, _ = optional_annotation  # tuple (annotation_type, None)
            new_field = FieldInfo(annotation=field_type)
        if type(new_field.annotation) is type(BaseModel):
            partial_inner_model = partial_model(cast("type[BaseModel]", new_field.annotation))
            partial_fields[field_name] = (
                partial_inner_model | None,
                FieldInfo(annotation=partial_inner_model, default=None),
            )
        else:
            partial_fields[field_name] = make_field_optional(new_field)
    # enable validation for unrecognized fields
    partial_fields["model_config"] = ConfigDict(extra="forbid")  # type: ignore[assignment]

    return create_model(  # type: ignore[call-overload]
        f"Partial{model.__name__}",
        __base__=model,
        __module__=model.__module__,
        **partial_fields,
    )
