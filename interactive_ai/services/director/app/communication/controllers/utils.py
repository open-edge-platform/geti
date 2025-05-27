# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


def delete_none_from_dict(d: dict) -> dict:
    """
    Remove None values recursively from dictionaries.

    :param d: Dictionary to process
    :return: Dictionary with None values removed
    """
    for key, value in list(d.items()):
        if isinstance(value, dict):
            delete_none_from_dict(value)
        elif value is None:
            del d[key]
        elif isinstance(value, list):
            for v_i in value:
                if isinstance(v_i, dict):
                    delete_none_from_dict(v_i)
    return d


def merge_deep_dict(a: dict, b: dict) -> dict:
    """
    Recursively merge dictionaries 'b' into 'a' with deep dictionary support.

    This method merges keys and values from dictionary 'b' into dictionary 'a'.
    For nested dictionaries, it performs a recursive merge. For all other value types,
    values from 'b' overwrite values in 'a' when keys exist in both dictionaries.

    Example:
        a = {'x': 1, 'y': {'a': 2}}
        b = {'y': {'b': 3}, 'z': 4}
        result = {'x': 1, 'y': {'a': 2, 'b': 3}, 'z': 4}

    :param a: Target dictionary to merge into (modified in-place)
    :param b: Source dictionary whose values will be merged into 'a'
    :return: The modified dictionary 'a' containing merged values from 'b'
    """
    for key, val in b.items():
        if key in a:
            if isinstance(a[key], dict) and isinstance(val, dict):
                merge_deep_dict(a[key], val)
            else:
                a[key] = val
        else:
            a[key] = val
    return a
