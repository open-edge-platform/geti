// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

export const useDatasetViewsQuery = () => {
    const projectId = useProjectIdentifier();
    return $api.useSuspenseQuery('get', '/api/projects/{project_id}/dataset/views', {
        params: {
            path: {
                project_id: projectId,
            },
        },
    });
};
