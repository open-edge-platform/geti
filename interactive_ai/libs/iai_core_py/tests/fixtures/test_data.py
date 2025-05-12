# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pathlib import Path

import pytest
import requests

URL_IAI_UNITTESTS = "http://s3.toolbox.iotg.sclab.intel.com/test/data/iai-unittests/"
URL_IMAGES = URL_IAI_UNITTESTS + "single_images/"
URL_VIDEO = URL_IAI_UNITTESTS + "video_repair_test/"
SAMPLE_IMAGE = "german_shepherd.jpg"
HEAT_MAP = "heatmap.npy"
REPAIRED_VIDEO = "repaired_video.mp4"
UNREPAIRABLE_VIDEO = "unrepairable_video.mp4"
REPAIRABLE_VIDEO = "repairable_video.mp4"


def download_file(url: str, file_path: Path) -> Path:
    response = requests.get(url=url)
    with open(file_path, "wb") as f:
        f.write(response.content)
    return file_path


@pytest.fixture(scope="session")
def fxt_test_data_path(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("iai-unittests")


@pytest.fixture(scope="session")
def fxt_sample_image(fxt_test_data_path) -> Path:
    url = URL_IMAGES + SAMPLE_IMAGE
    file_path: Path = fxt_test_data_path / SAMPLE_IMAGE
    return download_file(url=url, file_path=file_path)


@pytest.fixture(scope="session")
def fxt_sample_heatmap(fxt_test_data_path) -> Path:
    url = URL_IMAGES + HEAT_MAP
    file_path: Path = fxt_test_data_path / HEAT_MAP
    return download_file(url=url, file_path=file_path)


@pytest.fixture(scope="session")
def fxt_repaired_video(fxt_test_data_path) -> tuple[Path, float, int, int, int]:
    url = URL_VIDEO + REPAIRED_VIDEO
    file_path: Path = fxt_test_data_path / REPAIRED_VIDEO
    return download_file(url=url, file_path=file_path), 6.33, 640, 360, 133  # path, fps, width, height, total_frames


@pytest.fixture(scope="session")
def fxt_repairable_video(fxt_test_data_path) -> Path:
    url = URL_VIDEO + REPAIRABLE_VIDEO
    file_path: Path = fxt_test_data_path / REPAIRABLE_VIDEO
    return download_file(url=url, file_path=file_path)


@pytest.fixture(scope="session")
def fxt_unrepairable_video(fxt_test_data_path) -> Path:
    url = URL_VIDEO + UNREPAIRABLE_VIDEO
    file_path: Path = fxt_test_data_path / UNREPAIRABLE_VIDEO
    return download_file(url=url, file_path=file_path)
