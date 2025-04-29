// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useQuery } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { TaskIdentifier } from '../dtos/dataset-statistics.interface';
import { AllTasksDatasetStatistics, DatasetStatistics } from '../services/dataset-statistics.interface';

interface TaskDatasetStatisticsQueryOptions extends TaskIdentifier {
    enabled: boolean;
}

export const useDatasetStatistics = (
    { allTasksStatisticsEnabled }: { allTasksStatisticsEnabled: boolean } = { allTasksStatisticsEnabled: false }
) => {
    const { datasetStatisticsService } = useApplicationServices();

    const useGetAllTaskDatasetStatistics = ({ organizationId, workspaceId, projectId, datasetId }: TaskIdentifier) => {
        return useQuery<AllTasksDatasetStatistics, AxiosError>({
            queryKey: QUERY_KEYS.ALL_TASKS_DATASET_STATISTICS_KEY(projectId, datasetId),
            queryFn: () =>
                datasetStatisticsService.getAllTasksDatasetStatistics({
                    organizationId,
                    workspaceId,
                    projectId,
                    datasetId,
                    taskId: null,
                }),
            enabled: allTasksStatisticsEnabled,
            meta: { notifyOnError: true },
        });
    };

    const useGetTaskDatasetStatistics = ({
        organizationId,
        workspaceId,
        projectId,
        datasetId,
        taskId,
        enabled,
    }: TaskDatasetStatisticsQueryOptions) => {
        return useQuery<DatasetStatistics, AxiosError>({
            queryKey: QUERY_KEYS.DATASET_STATISTICS_KEY(projectId, datasetId, taskId ?? ''),
            queryFn: () =>
                datasetStatisticsService.getDatasetStatistics({
                    organizationId,
                    workspaceId,
                    projectId,
                    datasetId,
                    taskId,
                }),
            meta: { notifyOnError: true },
            enabled,
        });
    };

    return {
        useGetTaskDatasetStatistics,
        useGetAllTaskDatasetStatistics,
    };
};
