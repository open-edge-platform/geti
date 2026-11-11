// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { useQueryClient } from '@tanstack/react-query';
import { datasetViewsQueryOptions } from 'hooks/api/dataset-views.hook';

export const useDeleteDatasetViewMutation = () => {
    const queryClient = useQueryClient();

    return $api.useMutation('delete', '/api/projects/{project_id}/dataset/views/{dataset_view_id}', {
        onSuccess: (_data, { params }) =>
            queryClient.invalidateQueries({
                queryKey: datasetViewsQueryOptions(params.path.project_id).queryKey,
            }),
    });
};
