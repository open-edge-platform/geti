// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { DatasetView } from '@/api/types';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

const DATASET_VIEWS: DatasetView[] = [
    { id: 'collection-one', name: 'Collection One', created_at: '', project_id: '' },
    { id: 'collection-two', name: 'Collection Two', created_at: '', project_id: '' },
];

export const useDatasetViewsQuery = () => {
    const projectId = useProjectIdentifier();

    return {
        data: DATASET_VIEWS,
    };

    return $api.useSuspenseQuery('get', '/api/projects/{project_id}/dataset/views', {
        params: {
            path: {
                project_id: projectId,
            },
        },
    });
};
