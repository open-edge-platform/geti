// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import {
    AllTaskDatasetStatisticsDTO,
    DatasetStatisticsDTO,
    TaskIdentifier,
} from '../dtos/dataset-statistics.interface';
import { AllTasksDatasetStatistics, DatasetStatistics, DatasetStatisticsService } from './dataset-statistics.interface';
import { getAllTaskDatasetStatisticsDTO, getDatasetStatisticsEntity } from './utils';

export const createApiDatasetStatisticsService: CreateApiService<DatasetStatisticsService> = (
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
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
