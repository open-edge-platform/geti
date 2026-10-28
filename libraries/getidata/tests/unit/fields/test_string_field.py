from typing import Annotated

import pytest

from getidata.dataset import Dataset, Sample
from getidata.fields import string_field


@pytest.mark.parametrize(
    "text",
    [
        "Hello world",
        "",
        "   Leading and trailing spaces   ",
        "Special characters !@#$%^&*()_+-=[]{}|;':,.<>/?`~",
        "Multiline\nText\nWith\nNewlines",
        "Unicode characters: 你好，世界！👋🌍",
    ],
)
def test_string_field_roundtrip(text):
    class StringSample(Sample):
        text: Annotated[str, string_field(semantic="text")]

    ds = Dataset(StringSample)

    s = StringSample(text=text)
    ds.append(s)

    assert len(ds) == 1
    out = ds[0]
    assert isinstance(out, StringSample)
    assert out.text == text


def test_string_field_list_roundtrip():
    class MultiStringSample(Sample):
        texts: Annotated[list[str], string_field(is_list=True, semantic="texts")]

    ds = Dataset(MultiStringSample)

    texts = ["Hello world", "Good bye world"]
    s = MultiStringSample(texts=texts)
    ds.append(s)

    assert len(ds) == 1
    out = ds[0]
    assert isinstance(out, MultiStringSample)
    assert isinstance(out.texts, list)
    assert out.texts == texts
