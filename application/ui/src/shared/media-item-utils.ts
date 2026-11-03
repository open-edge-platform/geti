// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Media, MediaImage, MediaVideo, MediaVideoFrame, PredictionVideoRangePayload } from '@/api/types';

import { getMediaBinaryUrl } from './media-url.utils';

export const isVideo = (media: Pick<Media, 'type'> | undefined): media is MediaVideo => media?.type === 'video';

export const isVideoFrame = (media: Pick<Media, 'type'> | undefined): media is MediaVideoFrame =>
    media?.type === 'video_frame';

export const isImage = (media: Pick<Media, 'type'> | undefined): media is MediaImage => media?.type === 'image';

// The helpers below translate a media item (an image or a single video frame) into the shapes the API expects, so
// callers never branch on how each media type is addressed.
// TODO(#7810): extend with the Z/C/T coordinates of OME-TIFF / OME-Zarr images.

// Frames of the same video share the video's id, so the frame number is needed to tell them apart.
export const getMediaItemKey = (media: Media): string =>
    isVideoFrame(media) ? `${media.id}-${media.frame_number}` : media.id;

// Query params for the endpoints that act on a single media item: binary, thumbnail, annotations and embeddings.
export const getMediaItemQueryParams = (media: Media): { frame_index: number } | undefined =>
    isVideoFrame(media) ? { frame_index: media.frame_number } : undefined;

export const getMediaItemBinaryUrl = (projectId: string, media: Media): string => {
    const url = getMediaBinaryUrl(projectId, media.id);
    const queryParams = getMediaItemQueryParams(media);

    if (queryParams === undefined) {
        return url;
    }

    const searchParams = new URLSearchParams(Object.entries(queryParams).map(([key, value]) => [key, String(value)]));

    return `${url}?${searchParams}`;
};

// Predictions are requested by range; a single video frame is a one-frame range. Every caller must build it here so
// that fetching, prefetching and "is fetching" checks share the same query key.
export const getMediaItemPredictionRange = (media: Media): PredictionVideoRangePayload | null =>
    isVideoFrame(media)
        ? { start_frame: media.frame_number, end_frame: media.frame_number, stride: media.frame_stride }
        : null;
