// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo } from 'react';

import { $api } from '@/api';
import type { Media, MediaDTO } from '@/api/types';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { getErrorMessage } from '../../../query-client/query-client';

// We will never get the video frame using '/api/projects/{project_id}/dataset/media/{media_id}',
// it's added only because of documentation reasons. We use MediaVideoFrame as a local type to
// work with the played frame in the video. Mirrors `getMediaEntities` in
// `use-get-dataset-media-items.hook.ts`.
const getMediaEntity = (item: MediaDTO): Media => {
    if (item.type === 'video_frame') {
        return {
            duration: 0,
            frame_count: 0,
            annotated_frame_count: 0,
            fps: 0,
            frame_number: 0,
            frame_stride: 0,
            ...item,
        };
    }

    return item;
};

interface UseGetDatasetMediaItemOptions {
    enabled?: boolean;
}

export const useGetDatasetMediaItem = (mediaId: string | undefined, options?: UseGetDatasetMediaItemOptions) => {
    const projectId = useProjectIdentifier();

    const { data, isPending, isError, error } = $api.useQuery(
        'get',
        '/api/projects/{project_id}/dataset/media/{media_id}',
        { params: { path: { project_id: projectId, media_id: String(mediaId) } } },
        { enabled: Boolean(mediaId) && (options?.enabled ?? true) }
    );

    const mediaItem = useMemo(() => (data === undefined ? null : getMediaEntity(data)), [data]);
    const errorMessage = useMemo(() => (isError ? getErrorMessage(error) : null), [isError, error]);

    return { mediaItem, isPending, isError, errorMessage };
};
