# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from copy import deepcopy
from typing import Any, Optional

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo


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

    See https://stackoverflow.com/questions/67699451/make-every-field-as-optional-with-pydantic/76560886#76560886
    """

    def make_field_optional(field: FieldInfo, default: Any = None) -> tuple[Any, FieldInfo]:
        new = deepcopy(field)
        new.default = default
        new.annotation = Optional[field.annotation]  # type: ignore[assignment]  # noqa: UP007
        return new.annotation, new

    return create_model(  # type: ignore[call-overload]
        f"Partial{model.__name__}",
        __base__=model,
        __module__=model.__module__,
        **{field_name: make_field_optional(field_info) for field_name, field_info in model.model_fields.items()},
    )
