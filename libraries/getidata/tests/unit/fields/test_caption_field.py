from typing_extensions import Annotated

from getidata.dataset import Dataset, Sample
from getidata.fields.annotations import caption_field


def test_caption_field_single_roundtrip():
    class CaptionSample(Sample):
        caption: Annotated[str, caption_field()]

    ds = Dataset(CaptionSample)

    text = "A cat sitting on a mat."
    s = CaptionSample(caption=text)
    ds.append(s)

    assert len(ds) == 1
    out = ds[0]
    assert isinstance(out, CaptionSample)
    assert out.caption == text


def test_caption_field_list_roundtrip():
    class MultiCaptionSample(Sample):
        captions: Annotated[list[str], caption_field(is_list=True)]

    ds = Dataset(MultiCaptionSample)

    texts = ["A cat on a mat", "The feline rests", "Domestic cat lounging"]
    s = MultiCaptionSample(captions=texts)
    ds.append(s)

    assert len(ds) == 1
    out = ds[0]
    assert isinstance(out, MultiCaptionSample)
    assert isinstance(out.captions, list)
    assert out.captions == texts
