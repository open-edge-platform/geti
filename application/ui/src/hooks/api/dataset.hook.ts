// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

export const useDatasetStatistics = () => {
    const projectId = useProjectIdentifier();

    return $api.useSuspenseQuery('get', '/api/projects/{project_id}/dataset/statistics', {
        params: { path: { project_id: projectId } },
    });
};

// Non suspending variant, for places where the statistics are optional and should not block rendering
export const useDatasetStatisticsQuery = () => {
    const projectId = useProjectIdentifier();

    return $api.useQuery('get', '/api/projects/{project_id}/dataset/statistics', {
        params: { path: { project_id: projectId } },
    });
};
