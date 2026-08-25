// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { DatasetView } from '../type';

const DATASET_VIEWS: DatasetView[] = [
    { id: 'collection-one', name: 'Collection One' },
    { id: 'collection-two', name: 'Collection Two' },
];

export const useDatasetViewsQuery = () => {
    return {
        data: DATASET_VIEWS,
    };

    /*
    const projectId = useProjectIdentifier();
    return $api.useSuspenseQuery('get', '/api/projects/{project_id}/dataset/views', {
        params: {
            path: {
                project_id: projectId,
            },
        },
    });*/
};
