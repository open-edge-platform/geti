#!#!/usr/bin/env -S uv run --script
#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
import argparse
import asyncio
import json
import time
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx


async def stream_file(client, url, filename, semaphore):
    if Path(filename).exists():
        print(f"Skipping already downloaded {filename}")
        return

    async with semaphore:
        start_time = time.time()
        total_bytes = 0
        async with client.stream("GET", url) as stream:
            with Path(filename).open("wb") as file:
                async for data in stream.aiter_bytes():
                    file.write(data)
                    total_bytes += len(data)
        end_time = time.time()
        download_time = end_time - start_time
        total_bytes /= 1024 * 1024

        speed_mbps = total_bytes / download_time if download_time > 0 else 0
        print(f"Downloaded {url} - {total_bytes:.2f} MB in {download_time:.2f}s ({speed_mbps:.2f} MB/s)")


async def download_single_image(client, url, filename):
    image = await client.get(url)
    Path(filename).write_bytes(image.content)


async def download_images(data_dir):
    async with httpx.AsyncClient(timeout=20.0) as client:
        COCO128_URL = "https://storage.geti.intel.com/geti_predict/test/images/coco128.zip"
        archive = await client.get(COCO128_URL, follow_redirects=True)
        with ZipFile(BytesIO(archive.content)) as zfile:
            zfile.extractall(data_dir)

        image_downloads = [
            (
                "https://storage.geti.intel.com/geti_predict/test/images/BloodImage_00007.jpg",
                data_dir / "BloodImage_00007.jpg",
            ),
            ("https://storage.geti.intel.com/geti_predict/test/images/cards.png", data_dir / "cards.png"),
        ]

        await asyncio.gather(*[download_single_image(client, url, filename) for url, filename in image_downloads])


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--data_dir",
        type=Path,
        required=True,
        help="Directory to store downloaded models and datasets",
    )
    parser.add_argument(
        "-j",
        "--json_path",
        type=Path,
        required=True,
        help="Path to the JSON file with model information",
    )
    parser.add_argument(
        "-l",
        "--legacy",
        action="store_true",
        help="Download models using legacy directory structure (used in public_scope.json",
    )
    args = parser.parse_args()

    with args.json_path.open("r") as f:
        models_data = json.load(f)

    base_path = "https://storage.geti.intel.com/geti_predict/test/"
    semaphore = asyncio.Semaphore(10)
    args.data_dir.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=60.0) as client:
        tasks = []

        model_names = []
        for model_data in models_data:
            model_names.append(model_data["name"])
            if args.legacy and "encoder" in model_data:
                model_names.append(model_data["encoder"])
            if args.legacy and "extra_model" in model_data:
                model_names.append(model_data["extra_model"])

        for model_name in model_names:
            download_url = base_path + model_name
            if args.legacy:
                if model_name.endswith(".onnx"):
                    download_url = base_path + model_name.replace(".", "/model.")
                else:
                    download_url = base_path + model_name.replace(".", "/openvino.")
            save_path = args.data_dir / model_name
            save_path.parent.mkdir(parents=True, exist_ok=True)

            tasks.append(stream_file(client, download_url, save_path, semaphore))

            if model_name.endswith(".xml"):
                tasks.append(
                    stream_file(client, download_url.replace(".xml", ".bin"), save_path.with_suffix(".bin"), semaphore),
                )

        tasks.append(download_images(args.data_dir))

        print(f"Starting download of {len(tasks)} files with max 10 concurrent downloads...")
        await asyncio.gather(*tasks)
        print(f"All {len(tasks)} files downloaded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
