// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { useQueryClient } from '@tanstack/react-query';

import { getQueryKey } from '../../../../../../query-client/query-client';

export const useUnassignMediaFromViewMutation = () => {
    const queryClient = useQueryClient();

    return $api.useMutation('delete', '/api/projects/{project_id}/dataset/views/{dataset_view_id}/media', {
        onSuccess: (_data, { params }) => {
            const { project_id } = params.path;

            return Promise.all([
                queryClient.invalidateQueries({
                    queryKey: getQueryKey([
                        'get',
                        '/api/projects/{project_id}/dataset/media',
                        { params: { path: { project_id } } },
                    ]),
                }),
                queryClient.invalidateQueries({
                    queryKey: getQueryKey([
                        'get',
                        '/api/projects/{project_id}/dataset/items',
                        { params: { path: { project_id } } },
                    ]),
                }),
            ]);
        },
    });
};
