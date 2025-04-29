# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from utils.enums import CreditSystemTimeBoundaries


def is_whitespace_or_empty_string(input_str: str) -> bool:
    """
    This function takes a string as input and returns True
    if the string contains only whitespace characters or is empty, otherwise it returns False.
    """
    return input_str.isspace() or len(input_str) == 0


def validate_timestamp(timestamp: int, name: str) -> None:
    """
    Validates that a timestamp is within the credit system's operational period.

    Args:
        timestamp: Unix timestamp in milliseconds.
        name: Parameter name for error messages.
    """
    if not isinstance(timestamp, int):
        raise ValueError(f"{name} has to be integer")

    if timestamp < CreditSystemTimeBoundaries.START.value:
        raise ValueError(f"{name} must represent a date after April 1, 2024.")

    if timestamp > CreditSystemTimeBoundaries.END.value:
        raise ValueError(f"{name} must represent a date before April 2, 2224.")
