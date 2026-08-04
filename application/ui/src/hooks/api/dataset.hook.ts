// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

const datasetStatisticsQueryKey = (projectId: string) =>
    ['get', '/api/projects/{project_id}/dataset/statistics', { params: { path: { project_id: projectId } } }] as const;

export const useDatasetStatistics = () => {
    const projectId = useProjectIdentifier();

    return $api.useSuspenseQuery(...datasetStatisticsQueryKey(projectId));
};

// Non suspending variant, for places where the statistics are optional and should not block rendering
export const useDatasetStatisticsQuery = (enabled = true) => {
    const projectId = useProjectIdentifier();

    return $api.useQuery(...datasetStatisticsQueryKey(projectId), { enabled });
};
