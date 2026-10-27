// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Media, MediaImage, MediaVideo, MediaVideoFrame } from '@/api/types';

export const isVideo = (media: Pick<Media, 'type'> | undefined): media is MediaVideo => media?.type === 'video';

export const isVideoFrame = (media: Pick<Media, 'type'> | undefined): media is MediaVideoFrame =>
    media?.type === 'video_frame';

export const isImage = (media: Pick<Media, 'type'> | undefined): media is MediaImage => media?.type === 'image';

// Frames of the same video share the video's id, so the frame number is needed to tell them apart.
export const getMediaItemKey = (media: Media): string =>
    isVideoFrame(media) ? `${media.id}-${media.frame_number}` : media.id;
