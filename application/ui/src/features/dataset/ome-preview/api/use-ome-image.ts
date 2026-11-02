// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import type { OmeChannelDisplaySetting } from '@/api/types';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

const useMediaPathParams = (mediaId: string) => {
    const projectId = useProjectIdentifier();

    return { params: { path: { project_id: projectId, media_id: mediaId } } };
};

export const useOmeImageInfo = (mediaId: string) =>
    $api.useQuery('get', '/api/projects/{project_id}/dataset/media/{media_id}/ome', useMediaPathParams(mediaId));

export const useOmeChannelView = (mediaId: string) =>
    $api.useQuery(
        'get',
        '/api/projects/{project_id}/dataset/media/{media_id}/channel-view',
        useMediaPathParams(mediaId)
    );

export const useAnnotatedOmePlanes = (mediaId: string) =>
    $api.useQuery('get', '/api/projects/{project_id}/dataset/media/{media_id}/planes', {
        params: { ...useMediaPathParams(mediaId).params, query: { limit: 1000 } },
    });

export const useUpdateOmeChannelView = (mediaId: string) => {
    const pathParams = useMediaPathParams(mediaId);
    const mutation = $api.useMutation('put', '/api/projects/{project_id}/dataset/media/{media_id}/channel-view', {
        meta: {
            invalidateQueries: [
                ['get', '/api/projects/{project_id}/dataset/media/{media_id}/channel-view', pathParams],
            ],
        },
    });

    const updateChannelView = (settings: OmeChannelDisplaySetting[]) =>
        mutation.mutateAsync({ ...pathParams, body: { settings } });

    return { updateChannelView, isPending: mutation.isPending, error: mutation.error };
};
