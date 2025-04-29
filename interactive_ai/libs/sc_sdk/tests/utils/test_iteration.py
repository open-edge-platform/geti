# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from collections.abc import Iterator

import pytest

from sc_sdk.utils.iteration import grouper, multi_map


@pytest.mark.ScSdkComponent
class TestIteration:
    def test_grouper_iterable(self) -> None:
        iterable = "ABCDEFGHIJK"
        grouped = grouper(iterable, chunk_size=3)

        assert isinstance(grouped, Iterator)
        assert next(grouped) == ["A", "B", "C"]
        assert next(grouped) == ["D", "E", "F"]
        assert next(grouped) == ["G", "H", "I"]
        assert next(grouped) == ["J", "K"]
        assert list(grouper(iterable, chunk_size=len(iterable))) == [list(iterable)]
        assert list(grouper(iterable, chunk_size=len(iterable) * 2)) == [list(iterable)]
        with pytest.raises(ValueError):
            list(grouper(iterable, chunk_size=-1))

    def test_grouper_generator(self) -> None:
        def fn_gen():
            yield from range(1, 11)

        grouped = grouper(fn_gen(), chunk_size=3)

        assert isinstance(grouped, Iterator)
        assert next(grouped) == [1, 2, 3]
        assert next(grouped) == [4, 5, 6]
        assert next(grouped) == [7, 8, 9]
        assert next(grouped) == [10]
        assert list(grouper(fn_gen(), chunk_size=10)) == [list(fn_gen())]
        assert list(grouper(fn_gen(), chunk_size=20)) == [list(fn_gen())]

    def test_multi_map(self) -> None:
        in_sequence = [1, 2, 3, 4]

        out_sequence = list(multi_map(in_sequence, lambda x: x**2, lambda x: x + 1))

        assert out_sequence == [2, 5, 10, 17]
