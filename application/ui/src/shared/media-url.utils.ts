// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { API_BASE_URL } from '@/api';
import type { MediaOmePlane } from '@/api/types';

// Use plain string concatenation instead of `new URL(path, base)`. The latter
// requires an absolute base, but `API_BASE_URL` is an empty string when the UI
// is served from the same origin as the backend (the default in Docker).
const apiPath = (path: string) => `${API_BASE_URL.replace(/\/$/, '')}/api/${path}`;

export const getProjectThumbnailUrl = (projectId: string) => apiPath(`projects/${projectId}/thumbnail`);

const getMediaBaseUrl = (projectId: string, itemId: string) => apiPath(`projects/${projectId}/dataset/media/${itemId}`);

const getDatasetRevisionItemBaseUrl = (projectId: string, datasetRevisionId: string, itemId: string) =>
    apiPath(`projects/${projectId}/dataset_revisions/${datasetRevisionId}/items/${itemId}`);

export const getThumbnailUrl = (projectId: string, itemId: string) => `${getMediaBaseUrl(projectId, itemId)}/thumbnail`;

export const getMediaBinaryUrl = (projectId: string, itemId: string) => `${getMediaBaseUrl(projectId, itemId)}/binary`;

export const getMediaDownloadUrl = (projectId: string, itemId: string) =>
    `${getMediaBaseUrl(projectId, itemId)}/binary?raw=true`;

export const getDatasetRevisionThumbnailUrl = (projectId: string, datasetRevisionId: string, itemId: string) =>
    `${getDatasetRevisionItemBaseUrl(projectId, datasetRevisionId, itemId)}/thumbnail`;

export const getVideoFrameThumbnailUrl = (projectId: string, itemId: string, frameNumber: number) =>
    `${getMediaBaseUrl(projectId, itemId)}/thumbnail?frame_index=${frameNumber}`;

// `c` overrides the stored channel view with `<index>|<min>:<max>$<RRGGBB>` per shown channel. Without channels
// (view not loaded yet) it is omitted, so the server renders the stored view.
export const getOmeRenderUrl = (
    projectId: string,
    { id, z_index, t_index, channels }: Pick<MediaOmePlane, 'id' | 'z_index' | 't_index' | 'channels'>
) => {
    const searchParams = new URLSearchParams({ z: String(z_index), t: String(t_index) });

    if (channels.length > 0) {
        const c = channels
            .filter(({ enabled }) => enabled)
            // Integer windows so slider positions share cache entries
            .map(
                ({ channel, window_min, window_max, color }) =>
                    `${channel}|${Math.round(window_min)}:${Math.round(window_max)}$${color.replace('#', '').toUpperCase()}`
            )
            .join(',');

        searchParams.set('c', c);
    }

    return `${getMediaBaseUrl(projectId, id)}/render?${searchParams}`;
};
