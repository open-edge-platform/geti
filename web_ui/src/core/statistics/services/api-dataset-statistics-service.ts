// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';

import { CreateApiService } from '../../../../packages/core/src/services/create-api-service.interface';
import { API_URLS } from '../../../../packages/core/src/services/urls';
import {
    AllTaskDatasetStatisticsDTO,
    DatasetStatisticsDTO,
    TaskIdentifier,
} from '../dtos/dataset-statistics.interface';
import { AllTasksDatasetStatistics, DatasetStatistics, DatasetStatisticsService } from './dataset-statistics.interface';
import { getAllTaskDatasetStatisticsDTO, getDatasetStatisticsEntity } from './utils';

export const createApiDatasetStatisticsService: CreateApiService<DatasetStatisticsService> = (
    { instance, router } = { instance: apiClient, router: API_URLS }
) => {
    const getAllTasksDatasetStatistics = async ({
        organizationId,
        workspaceId,
        projectId,
        datasetId,
    }: TaskIdentifier): Promise<AllTasksDatasetStatistics> => {
        const { data } = await instance.get<AllTaskDatasetStatisticsDTO>(
            router.ANNOTATIONS_STATISTICS({ organizationId, workspaceId, projectId, datasetId, taskId: null })
        );

        return getAllTaskDatasetStatisticsDTO(data);
    };

    const getDatasetStatistics = async ({
        organizationId,
        workspaceId,
        projectId,
        datasetId,
        taskId,
    }: TaskIdentifier): Promise<DatasetStatistics> => {
        const { data } = await instance.get<DatasetStatisticsDTO>(
            router.ANNOTATIONS_STATISTICS({ organizationId, workspaceId, projectId, datasetId, taskId })
        );

        return getDatasetStatisticsEntity(data);
    };
    return { getDatasetStatistics, getAllTasksDatasetStatistics };
};
