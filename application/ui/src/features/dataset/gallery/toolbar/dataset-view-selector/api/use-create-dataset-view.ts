// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { useQueryClient } from '@tanstack/react-query';

import { getQueryKey } from '../../../../../../query-client/query-client';

export const useCreateDatasetViewMutation = () => {
    const queryClient = useQueryClient();

    return $api.useMutation('post', '/api/projects/{project_id}/dataset/views', {
        onSuccess: ({ project_id }) => {
            return queryClient.invalidateQueries({
                queryKey: getQueryKey([
                    'get',
                    '/api/projects/{project_id}/dataset/views',
                    {
                        params: {
                            path: {
                                project_id,
                            },
                        },
                    },
                ]),
            });
        },
    });
};
