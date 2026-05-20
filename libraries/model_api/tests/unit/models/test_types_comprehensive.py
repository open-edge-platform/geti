# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from model_api.models.types import (
    BaseValue,
    BooleanValue,
    ConfigurableValueError,
    DictValue,
    ListValue,
    NumericalValue,
    StringValue,
    get_python_type,
)

# --- ConfigurableValueError ---


def test_configurable_value_error_with_prefix():
    err = ConfigurableValueError("bad value", prefix="param_x")
    assert "param_x: bad value" in str(err)


def test_configurable_value_error_without_prefix():
    err = ConfigurableValueError("bad value")
    assert str(err) == "bad value"


# --- BaseValue ---


def test_base_value_init():
    bv = BaseValue(description="test desc", default_value=42)
    assert bv.description == "test desc"
    assert bv.default_value == 42


def test_base_value_update_default():
    bv = BaseValue()
    bv.update_default_value(99)
    assert bv.default_value == 99


def test_base_value_validate():
    bv = BaseValue()
    assert bv.validate("anything") == []


def test_base_value_get_value():
    bv = BaseValue(default_value=10)
    assert bv.get_value(5) == 5
    assert bv.get_value(None) == 10


def test_base_value_build_error():
    bv = BaseValue()
    assert bv.build_error() is None


def test_base_value_str_with_default():
    bv = BaseValue(description="my desc", default_value="hello")
    s = str(bv)
    assert "my desc" in s
    assert "hello" in s


def test_base_value_str_without_default():
    bv = BaseValue(description="my desc")
    s = str(bv)
    assert "my desc" in s


# --- NumericalValue ---


def test_numerical_value_init():
    nv = NumericalValue(value_type=int, min=0, max=100, description="count")
    assert nv.value_type is int
    assert nv.min == 0
    assert nv.max == 100


def test_numerical_from_str_empty_with_default():
    nv = NumericalValue(default_value=5.0)
    assert nv.from_str("") == 5.0


def test_numerical_from_str_empty_no_default():
    nv = NumericalValue(default_value=None)
    assert nv.from_str("") is None


def test_numerical_from_str_none():
    nv = NumericalValue()
    assert nv.from_str("None") is None


def test_numerical_from_str_numeric():
    nv = NumericalValue(value_type=int)
    assert nv.from_str("42") == 42


def test_numerical_validate_type_error():
    nv = NumericalValue(value_type=int)
    errors = nv.validate("not a number")
    assert len(errors) > 0


def test_numerical_validate_choices():
    nv = NumericalValue(value_type=int, choices=(1, 2, 3))
    errors = nv.validate(5)
    assert len(errors) > 0


def test_numerical_validate_min():
    nv = NumericalValue(value_type=float, min=0.0)
    errors = nv.validate(-1.0)
    assert len(errors) > 0


def test_numerical_validate_max():
    nv = NumericalValue(value_type=float, max=10.0)
    errors = nv.validate(20.0)
    assert len(errors) > 0


def test_numerical_validate_ok():
    nv = NumericalValue(value_type=float, min=0.0, max=10.0)
    errors = nv.validate(5.0)
    assert len(errors) == 0


def test_numerical_str():
    nv = NumericalValue(value_type=int, choices=(1, 2), description="pick")
    s = str(nv)
    assert "int" in s
    assert "(1, 2)" in s


# --- StringValue ---


def test_string_value_init():
    sv = StringValue(choices=("a", "b"), default_value="a")
    assert sv.choices == ("a", "b")
    assert sv.default_value == "a"


def test_string_from_str():
    sv = StringValue()
    assert sv.from_str("hello") == "hello"
    assert sv.from_str("None") is None


def test_string_validate_type_error():
    sv = StringValue()
    errors = sv.validate(123)
    assert len(errors) > 0


def test_string_validate_choices():
    sv = StringValue(choices=("a", "b"))
    errors = sv.validate("c")
    assert len(errors) > 0


def test_string_validate_ok():
    sv = StringValue(choices=("a", "b"))
    assert len(sv.validate("a")) == 0


def test_string_str():
    sv = StringValue(choices=("x", "y"), description="letter")
    s = str(sv)
    assert "str" in s
    assert "('x', 'y')" in s


def test_string_value_bad_choice():
    with pytest.raises(ValueError, match="Incorrect option"):
        StringValue(choices=(1, 2))


# --- BooleanValue ---


def test_boolean_from_str_yes():
    bv = BooleanValue()
    assert bv.from_str("YES") is True


def test_boolean_from_str_true():
    bv = BooleanValue()
    assert bv.from_str("True") is True


def test_boolean_from_str_false():
    bv = BooleanValue()
    assert bv.from_str("False") is False


def test_boolean_from_str_none():
    bv = BooleanValue()
    assert bv.from_str("None") is None


def test_boolean_validate_type_error():
    bv = BooleanValue()
    errors = bv.validate("not bool")
    assert len(errors) > 0


def test_boolean_validate_ok():
    bv = BooleanValue()
    val = True
    assert len(bv.validate(val)) == 0


# --- ListValue ---


def test_list_from_str_none():
    lv = ListValue()
    assert lv.from_str("None") is None


def test_list_from_str_string_type():
    lv = ListValue(value_type=str)
    result = lv.from_str("a b c")
    assert result == ["a", "b", "c"]


def test_list_from_str_float_values():
    lv = ListValue()
    result = lv.from_str("1.5 2.5 3.5")
    assert result == [1.5, 2.5, 3.5]


def test_list_from_str_int_values():
    lv = ListValue()
    result = lv.from_str("1 2 3")
    assert result == [1, 2, 3]


def test_list_from_str_mixed():
    lv = ListValue()
    result = lv.from_str("abc def")
    assert result == ["abc", "def"]


def test_list_validate_type_error():
    lv = ListValue()
    errors = lv.validate("not a list")
    assert len(errors) > 0


def test_list_validate_element_type():
    lv = ListValue(value_type=int)
    errors = lv.validate([1, "two", 3])
    assert len(errors) > 0


def test_list_validate_element_base_value():
    inner = NumericalValue(value_type=int, min=0)
    lv = ListValue(value_type=inner)
    errors = lv.validate([1, -1, 3])
    assert len(errors) > 0


def test_list_validate_ok():
    lv = ListValue(value_type=int)
    assert len(lv.validate([1, 2, 3])) == 0


# --- DictValue ---


def test_dict_from_str_raises():
    dv = DictValue()
    with pytest.raises(NotImplementedError):
        dv.from_str("anything")


def test_dict_validate_type_error():
    dv = DictValue()
    errors = dv.validate("not a dict")
    assert len(errors) > 0


def test_dict_validate_ok():
    dv = DictValue()
    assert len(dv.validate({"a": 1})) == 0


# --- get_python_type ---


def test_get_python_type_numerical():
    assert get_python_type(NumericalValue(value_type=int)) is int
    assert get_python_type(NumericalValue(value_type=float)) is float


def test_get_python_type_boolean():
    assert get_python_type(BooleanValue()) is bool


def test_get_python_type_string():
    assert get_python_type(StringValue()) is str


def test_get_python_type_list():
    assert get_python_type(ListValue()) is list


def test_get_python_type_dict():
    assert get_python_type(DictValue()) is dict


def test_get_python_type_base():
    assert get_python_type(BaseValue()) is object


# --- Validation error raising via get_value (types.py lines 36-37) ---


def test_numerical_value_get_value_raises_on_invalid_type():
    nv = NumericalValue()
    with pytest.raises(ValueError, match="Encountered errors"):
        nv.get_value("not_a_number")


def test_string_value_get_value_raises_on_invalid_type():
    sv = StringValue()
    with pytest.raises(ValueError, match="Encountered errors"):
        sv.get_value(12345)


def test_boolean_value_get_value_raises_on_invalid_type():
    bv = BooleanValue()
    with pytest.raises(ValueError, match="Encountered errors"):
        bv.get_value("not_bool")


def test_list_value_get_value_raises_on_invalid_type():
    lv = ListValue()
    with pytest.raises(ValueError, match="Encountered errors"):
        lv.get_value("not_a_list")


def test_dict_value_get_value_raises_on_invalid_type():
    dv = DictValue()
    with pytest.raises(ValueError, match="Encountered errors"):
        dv.get_value("not_a_dict")


# --- Validate returns early for falsy values (lines 76, 134, 170, 210, 251) ---


def test_numerical_value_validate_empty():
    nv = NumericalValue()
    errors = nv.validate(0)
    assert errors == []


def test_string_value_validate_empty():
    sv = StringValue()
    errors = sv.validate("")
    assert errors == []


def test_boolean_value_validate_none():
    bv = BooleanValue()
    errors = bv.validate(None)
    assert errors == []


def test_list_value_validate_empty():
    lv = ListValue()
    errors = lv.validate([])
    assert errors == []


def test_dict_value_validate_empty():
    dv = DictValue()
    errors = dv.validate({})
    assert errors == []
