# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from functools import partial

from iai_core_py.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core_py.configuration.elements.parameter_group import ParameterGroup
from iai_core_py.configuration.elements.primitive_parameters import (
    configurable_boolean,
    configurable_float,
    configurable_integer,
    float_selectable,
    selectable,
)
from iai_core_py.configuration.helper.config_element_mapping import (
    GroupElementMapping,
    PrimitiveElementMapping,
    RuleElementMapping,
)
from iai_core_py.configuration.ui_rules.rules import Rule, UIRules


class TestPrimitiveElementMapping:
    @staticmethod
    def check_primitive_element(
        primitive_element: PrimitiveElementMapping,
        expected_name: str,
        expected_partial_element: partial,
    ):
        assert primitive_element.name == expected_name
        assert str(primitive_element) == expected_name
        assert isinstance(primitive_element.value, partial)
        assert primitive_element.value.args == expected_partial_element.args
        assert primitive_element.value.keywords == expected_partial_element.keywords

    def test_primitive_element_mapping(self):
        """
        <b>Description:</b>
        Check "PrimitiveElementMapping" Enum class elements

        <b>Expected results:</b>
        Test passes if "PrimitiveElementMapping" Enum class length is equal to expected value and its elements have
        expected "value" and "name" attributes and value returned by "__str__" method
        """

        assert len(PrimitiveElementMapping) == 5
        self.check_primitive_element(
            primitive_element=PrimitiveElementMapping.INTEGER,
            expected_name="INTEGER",
            expected_partial_element=partial(configurable_integer),
        )
        self.check_primitive_element(
            primitive_element=PrimitiveElementMapping.FLOAT,
            expected_name="FLOAT",
            expected_partial_element=partial(configurable_float),
        )
        self.check_primitive_element(
            primitive_element=PrimitiveElementMapping.BOOLEAN,
            expected_name="BOOLEAN",
            expected_partial_element=partial(configurable_boolean),
        )
        self.check_primitive_element(
            primitive_element=PrimitiveElementMapping.FLOAT_SELECTABLE,
            expected_name="FLOAT_SELECTABLE",
            expected_partial_element=partial(float_selectable),
        )
        self.check_primitive_element(
            primitive_element=PrimitiveElementMapping.SELECTABLE,
            expected_name="SELECTABLE",
            expected_partial_element=partial(selectable),
        )


def check_mapping_element(mapping_element, expected_name, expected_value):
    assert mapping_element.name == expected_name
    assert mapping_element.value == expected_value
    assert str(mapping_element) == expected_name


class TestGroupElementMapping:
    def test_group_element_mapping(self):
        """
        <b>Description:</b>
        Check "GroupElementMapping" Enum class elements

        <b>Expected results:</b>
        Test passes if "GroupElementMapping" Enum class length is equal to expected value and its elements have
        expected "name" attribute and value returned by "__str__" method
        """
        assert len(GroupElementMapping) == 2
        check_mapping_element(
            mapping_element=GroupElementMapping.PARAMETER_GROUP,
            expected_name="PARAMETER_GROUP",
            expected_value=ParameterGroup,
        )
        check_mapping_element(
            mapping_element=GroupElementMapping.CONFIGURABLE_PARAMETERS,
            expected_name="CONFIGURABLE_PARAMETERS",
            expected_value=ConfigurableParameters,
        )


class TestRuleElementMapping:
    def test_group_element_mapping(self):
        """
        <b>Description:</b>
        Check "RuleElementMapping" Enum class elements

        <b>Expected results:</b>
        Test passes if "RuleElementMapping" Enum class length is equal to expected value and its elements have
        expected "name" attribute and value returned by "__str__" method
        """
        assert len(RuleElementMapping) == 2
        check_mapping_element(
            mapping_element=RuleElementMapping.RULE,
            expected_name="RULE",
            expected_value=Rule,
        )
        check_mapping_element(
            mapping_element=RuleElementMapping.UI_RULES,
            expected_name="UI_RULES",
            expected_value=UIRules,
        )
