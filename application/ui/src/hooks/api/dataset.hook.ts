// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { useQuery, useSuspenseQuery } from '@tanstack/react-query';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

const datasetStatisticsQueryOptions = (projectId: string) =>
    $api.queryOptions('get', '/api/projects/{project_id}/dataset/statistics', {
        params: { path: { project_id: projectId } },
    });

export const useDatasetStatistics = () => {
    const projectId = useProjectIdentifier();

    return useSuspenseQuery(datasetStatisticsQueryOptions(projectId));
};

// Non suspending variant, for places where the statistics are optional and should not block rendering
export const useDatasetStatisticsQuery = (enabled = true) => {
    const projectId = useProjectIdentifier();

    return useQuery({ ...datasetStatisticsQueryOptions(projectId), enabled });
};
