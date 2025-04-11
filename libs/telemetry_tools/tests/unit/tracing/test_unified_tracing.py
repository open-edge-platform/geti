# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

from geti_telemetry_tools import unified_tracing


class TestUnifiedTracing:
    def test_decorator_on_function(self) -> None:
        """Check that @unified_tracing does not raise errors when it wraps a function"""

        @unified_tracing
        def my_sum(a: int, b: int, /) -> int:
            return a + b

        assert my_sum(1, 2) == 3

    def test_decorator_on_class_method(self) -> None:
        """Check that @unified_tracing does not raise errors when it wraps a method"""

        class Adder:
            @unified_tracing
            def my_sum(self, a: int, b: int, /) -> int:
                return a + b

            @staticmethod
            @unified_tracing
            def my_sum_staticmethod(a: int, b: int, /) -> int:
                return a + b

            @classmethod
            @unified_tracing
            def my_sum_classmethod(cls, a: int, b: int, /) -> int:
                return a + b

        adder = Adder()
        assert adder.my_sum(1, 2) == 3
        assert adder.my_sum_staticmethod(1, 2) == 3
        assert adder.my_sum_classmethod(1, 2) == 3
