# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel


class MediaInfoPayload(BaseModel):
    dataset_storage_id: str
    image_id: str | None = None
    video_id: str | None = None
    frame_index: int | None = None
