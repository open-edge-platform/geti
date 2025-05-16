# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import hashlib
import logging
import os
import shutil
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable

logging.basicConfig(level=logging.INFO)

RETRIES = 5

logger = logging.getLogger(__name__)


def sha256sum(filepath: str):  # noqa: ANN201, D103
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def download_file(url: str, target_path: str, auto_unzip=True):  # noqa: ANN001, ANN201, D103
    logger.info(f"Downloading file: {url}")
    url_original_filename = os.path.basename(url)
    if "?" in url_original_filename:
        url_original_filename = url_original_filename.split("?")[0]

    target_dir_path = os.path.dirname(target_path)
    download_temp_target_path = os.path.join(target_dir_path, url_original_filename)

    with (
        urllib.request.urlopen(url) as response,  # noqa: S310
        open(download_temp_target_path, "wb") as out_file,
    ):
        shutil.copyfileobj(response, out_file)

    # do not use 'zipfile.is_zipfile'!
    # some '.pth' files are actually zip files and they should not be unzipped here
    if auto_unzip and download_temp_target_path.endswith(".zip"):
        with zipfile.ZipFile(download_temp_target_path) as zip_ref:
            files_in_zip = zip_ref.namelist()
            number_of_files_in_zip = len(files_in_zip)
            if number_of_files_in_zip != 1:
                raise RuntimeError(
                    f"Unexpected number of files: {number_of_files_in_zip}, expected: 1 in: {download_temp_target_path}"
                )
            zip_ref.extractall(target_dir_path)
        os.remove(download_temp_target_path)
        shutil.move(os.path.join(target_dir_path, files_in_zip[0]), target_path)
    elif os.path.dirname(download_temp_target_path) != os.path.dirname(target_path) or (
        os.path.basename(download_temp_target_path) != os.path.basename(target_path)
    ):
        shutil.move(download_temp_target_path, target_path)


class MaxTriesExhausted(Exception):
    pass


# no retry lib has been used here on purpose - to avoid installing additional libs
def retry_call(call: Callable, retries: int = RETRIES, **kwargs):  # noqa: ANN201, D103
    for i in range(retries):
        logger.info(f"Try {i + 1}/{retries}")
        try:
            call(**kwargs)
            break
        except Exception:
            logger.exception(f"Failed try {i + 1}/{retries}")
    else:
        raise MaxTriesExhausted


def download_pretrained_model(model_spec: dict, target_dir: str, weights_url: str | None = None):  # noqa: ANN201, D103
    model_external_url = model_spec["url"]
    target_path = model_spec["target"]
    auto_unzip = model_spec.get("unzip", True)
    sha_sum = model_spec.get("sha_sum")

    target_download_path = os.path.join(target_dir, os.path.basename(target_path))
    if weights_url is not None:
        model_external_url = os.path.join(weights_url, os.path.basename(model_external_url))

    if os.path.exists(target_download_path):
        if sha_sum is None:
            logger.warning(f"Model already existed: {target_download_path} but sha_sum is not specified")
            logger.warning(f"consider to add sha_sum to the model spec: {sha256sum(target_download_path)}")
        elif sha256sum(target_download_path) == sha_sum:
            logger.info(f"Model already downloaded: {target_download_path}")
            return
        else:
            logger.warning(f"Model already downloaded but SHA mismatch: {target_download_path}")
            logger.warning("Redownloading...")
            os.remove(target_download_path)

    try:
        retry_call(
            download_file,
            url=model_external_url,
            target_path=target_download_path,
            auto_unzip=auto_unzip,
        )
    except MaxTriesExhausted:
        raise

    # verify SHA
    if sha_sum is not None:
        received_sha = sha256sum(target_download_path)
        if sha_sum != received_sha:
            raise RuntimeError(f"Wrong SHA sum for: {target_download_path}. Expected: {sha_sum}, got: {received_sha}")
        logger.info("SHA match")
