"""
This module contains utility functions to convert and manipulate strings
"""

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

import re
import unicodedata


def camel_to_snake_case(name: str, preserve_acronyms: bool = False) -> str:
    """
    Convert a string from CamelCase to snake_case.

    In practice, every occurrence of an uppercase letter is replaced with the same
    letter but lowercase and preceded by an underscore. The only exception is the
    initial character of the string, where no underscore shall be prepended.

    Examples:
        FooBar  -> foo_bar
        fooBar  -> foo_bar
        foo_bar -> foo_bar
        FOOBar  -> f_o_o_bar  (w/o preserve_acronyms)
        FOOBar  -> foo_bar    (w/  preserve_acronyms)
        Foo_Bar -> foo__bar

    :param name: Input string
    :param preserve_acronyms: If True, sequences of consecutive uppercase letters
        will not be transformed. Only the final letter of the sequence is converted.
    :return: Converted string complying with the snake_case convention
    """
    if preserve_acronyms:
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def snake_to_camel_case(name: str, lower_camel_case: bool = False) -> str:
    """
    Convert a string from snake_case to CamelCase.

    In practice, every underscore is removed and the first letter (if any)
    following that underscore is capitalized.
    By default, the first char of the string is also capitalized (UpperCamelCase),
    but it's also possible to specify a lowerCamelCase behavior.

    Note: no letter will be forced to lowercase in the process, most notably when
        converting a string starting with a capital letter with lower_camel_case=True.

    Examples:
        foo_bar   -> FooBar (upper)
        foo_bar   -> fooBar (lower)
        fooBar    -> FooBar (upper)
        FooBar    -> FooBar
        Foobar_   -> Foobar
        _foo_bar  -> FooBar (upper)
        _foo_bar  -> fooBar (lower)
        Foo__bar  -> FooBar
        Foo___bar -> FooBar

    :param name: Input string
    :param lower_camel_case: if True, use lowerCamelCase instead of UpperCamelCase
    :return: Converted string complying with the UpperCamelCase or lowerCamelCase style
    """

    def _capitalize_word(word: str) -> str:
        return word[:1].upper() + word[1:]

    words = (w for w in name.split("_") if w)
    if lower_camel_case:
        return "".join(w if i == 0 else _capitalize_word(w) for i, w in enumerate(words))
    return "".join(_capitalize_word(w) for w in words)


def slugify(name: str) -> str:
    """
    Slugify a string, i.e. apply transformations so that it can be safely used in URLs or as a file name.

    Changes:
     - Convert spaces and repeated dashes to single dashes.
     - Remove characters that aren't alphanumerics, underscores, or hyphens.
     - Convert to lowercase.
     - strip leading and trailing whitespace, dashes, and underscores.

    :param name: Name to slugify
    """
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[-\s]+", "-", name).strip("-_")
