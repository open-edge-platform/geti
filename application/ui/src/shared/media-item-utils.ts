// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type {
    Media,
    MediaImage,
    MediaOmeImage,
    MediaOmePlane,
    MediaVideo,
    MediaVideoFrame,
    PredictionVideoRangePayload,
} from '@/api/types';

import { getMediaBinaryUrl, getOmeRenderUrl } from './media-url.utils';

export const isVideo = (media: Pick<Media, 'type'> | undefined): media is MediaVideo => media?.type === 'video';

export const isVideoFrame = (media: Pick<Media, 'type'> | undefined): media is MediaVideoFrame =>
    media?.type === 'video_frame';

export const isImage = (media: Pick<Media, 'type'> | undefined): media is MediaImage => media?.type === 'image';

export const isOmeImage = (media: Pick<Media, 'type'> | undefined): media is MediaOmeImage =>
    media?.type === 'ome_image';

export const isOmePlane = (media: Pick<Media, 'type'> | undefined): media is MediaOmePlane =>
    media?.type === 'ome_plane';

// Annotatable media is a single 2D picture that annotations, embeddings and predictions refer to directly (an image or
// a video frame). A video isn't: the annotator resolves it to one of its frames first. Same set as the backend's
// `LEAF_MEDIA_TYPES`. Positive on purpose, so a new media type stays non-annotatable until it is added here.
// TODO(#7810): include OME planes (one (Z, T) of an OME-TIFF / OME-Zarr image, all channels composited).
export const isAnnotatableMedia = (media: Pick<Media, 'type'> | undefined): media is MediaImage | MediaVideoFrame =>
    isImage(media) || isVideoFrame(media);

// The helpers below translate a media item (an image, a video frame or an OME plane) into the shapes the API expects,
// so callers never branch on how each media type is addressed.

// Frames of the same video and planes of the same OME image share their parent's id.
export const getMediaItemKey = (media: Media): string => {
    if (isVideoFrame(media)) {
        return `${media.id}-${media.frame_number}`;
    }

    if (isOmePlane(media)) {
        return `${media.id}-z${media.z_index}-t${media.t_index}`;
    }

    return media.id;
};

// Query params for the endpoints that act on a single media item: binary, thumbnail, annotations and embeddings.
// TODO(#7810): drop the optional `z`/`t` once the regenerated OpenAPI types include them.
export const getMediaItemQueryParams = (media: Media): { frame_index?: number; z?: number; t?: number } | undefined => {
    if (isVideoFrame(media)) {
        return { frame_index: media.frame_number };
    }

    if (isOmePlane(media)) {
        return { z: media.z_index, t: media.t_index };
    }

    return undefined;
};

// The picture the annotator shows: the stored file, or for an OME plane a render of its channel view.
export const getMediaItemImageUrl = (projectId: string, media: Media): string => {
    if (isOmePlane(media)) {
        return getOmeRenderUrl(projectId, media);
    }

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
