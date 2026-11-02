// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type {
    Media,
    MediaImage,
    MediaOmeImage,
    MediaOmePlane,
    MediaVideo,
    MediaVideoFrame,
    PredictionRangePayload,
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

// OME images, and the planes displayed from them, are opened in the dedicated OME annotator.
export const isOmeMedia = (media: Pick<Media, 'type'> | undefined): media is MediaOmeImage | MediaOmePlane =>
    isOmeImage(media) || isOmePlane(media);

// The helpers below translate a media item (an image, a single video frame or a single OME plane) into the shapes the
// API expects, so callers never branch on how each media type is addressed.

// Frames of the same video, and planes of the same OME image, share the parent's id, so the frame number (or the plane
// coordinates and rendering) is needed to tell them apart.
export const getMediaItemKey = (media: Media): string => {
    if (isVideoFrame(media)) {
        return `${media.id}-${media.frame_number}`;
    }

    if (isOmePlane(media)) {
        return `${media.id}-z${media.z_index}-t${media.t_index}-r${media.render_level}-${media.render_version}`;
    }

    return media.id;
};

type MediaItemQueryParams = { frame_index: number } | { z: number; t: number };

// Query params for the endpoints that act on a single media item: binary, thumbnail, annotations and embeddings.
export const getMediaItemQueryParams = (media: Media): MediaItemQueryParams | undefined => {
    if (isVideoFrame(media)) {
        return { frame_index: media.frame_number };
    }

    if (isOmePlane(media)) {
        return { z: media.z_index, t: media.t_index };
    }

    return undefined;
};

export const getMediaItemBinaryUrl = (projectId: string, media: Media): string => {
    // OME planes are displayed with the channel display settings chosen by the user, rendered server-side
    if (isOmePlane(media)) {
        return getOmeRenderUrl(projectId, media.id, {
            z: media.z_index,
            t: media.t_index,
            level: media.render_level,
            version: media.render_version,
        });
    }

    const url = getMediaBinaryUrl(projectId, media.id);
    const queryParams = getMediaItemQueryParams(media);

    if (queryParams === undefined) {
        return url;
    }

    const searchParams = new URLSearchParams(Object.entries(queryParams).map(([key, value]) => [key, String(value)]));

    return `${url}?${searchParams}`;
};

// Predictions are requested by range; a single video frame (or OME plane) is a one-item range. Every caller must build
// it here so that fetching, prefetching and "is fetching" checks share the same query key.
export const getMediaItemPredictionRange = (media: Media): PredictionRangePayload | null => {
    if (isVideoFrame(media)) {
        return { start_frame: media.frame_number, end_frame: media.frame_number, stride: media.frame_stride };
    }

    if (isOmePlane(media)) {
        return {
            z: { start: media.z_index, end: media.z_index, stride: 1 },
            t: { start: media.t_index, end: media.t_index, stride: 1 },
        };
    }

    return null;
};
