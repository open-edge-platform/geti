# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from iai_core.utils.naming_helpers import camel_to_snake_case, slugify, snake_to_camel_case


class TestNamingHelpers:
    def test_camel_to_snake_case(self) -> None:
        """
        <b>Description:</b>
        Test conversions from CamelCase to snake_case

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        The converter outputs the expected result strings for every test input string.

        <b>Steps</b>
        1. Define a bunch of test input strings
        2. Define the expected result for each test string
        3. Convert each test input using camel_to_snake_case, with and without
            the option to preserve acronyms.
        4. Compare the output strings with the expected ones
        """
        # (in_string, exp_result_without_pres_acronym, exp_result_with_pres_acronym)
        test_strings = (
            ("FooBar", "foo_bar", "foo_bar"),
            ("fooBar", "foo_bar", "foo_bar"),
            ("foo_bar", "foo_bar", "foo_bar"),
            ("FOOBar", "f_o_o_bar", "foo_bar"),
            ("Foo_Bar", "foo__bar", "foo__bar"),
        )
        for in_str, exp_out_without_preserve, exp_out_with_preserve in test_strings:
            out_without_preserve = camel_to_snake_case(in_str)
            assert out_without_preserve == exp_out_without_preserve, (
                f"Tried converting '{in_str}' (w/o preserve acronyms), "
                f"got '{out_without_preserve}', expected '{exp_out_without_preserve}'"
            )
            out_with_preserve = camel_to_snake_case(in_str, preserve_acronyms=True)
            assert out_with_preserve == exp_out_with_preserve, (
                f"Tried converting '{in_str}' (w/ preserve acronyms), "
                f"got '{out_with_preserve}', expected '{exp_out_with_preserve}'"
            )

    def test_snake_to_camel_case(self) -> None:
        """
        <b>Description:</b>
        Test conversions from snake_case to CamelCase

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        The converter outputs the expected result strings for every test input string.

        <b>Steps</b>
        1. Define a bunch of test input strings
        2. Define the expected result for each test string
        3. Convert each test input using snake_to_camel_case
        4. Compare the output strings with the expected ones
        """
        # (in_string, exp_result_upper_camel, exp_result_lower_camel)
        test_strings = (
            ("foo_bar", "FooBar", "fooBar"),
            ("fooBar", "FooBar", "fooBar"),
            ("FooBar", "FooBar", "FooBar"),
            ("Foobar_", "Foobar", "Foobar"),
            ("_foo_bar", "FooBar", "fooBar"),
            ("foo__bar", "FooBar", "fooBar"),
            ("foo___bar", "FooBar", "fooBar"),
        )
        for in_str, exp_out_upper, exp_out_lower in test_strings:
            out_str_upper = snake_to_camel_case(in_str)
            assert out_str_upper == exp_out_upper, (
                f"Tried converting '{in_str} (UpperCamelCase)', got '{out_str_upper}', expected '{exp_out_upper}'"
            )
            out_str_lower = snake_to_camel_case(in_str, lower_camel_case=True)
            assert out_str_lower == exp_out_lower, (
                f"Tried converting '{in_str} (lowerCamelCase)', got '{out_str_lower}', expected '{exp_out_lower}'"
            )

    def test_slugify(self) -> None:
        # (in_string, exp_result)
        test_strings = (
            ("foo", "foo"),
            ("name  with spaces", "name-with-spaces"),
            (" _-NAME-two-_ ", "name-two"),
            ("name_123_+'", "name_123"),
        )
        for in_str, exp_result in test_strings:
            result = slugify(in_str)
            assert result == exp_result, f"Tried converting '{in_str}', got '{result}', expected '{exp_result}'"
