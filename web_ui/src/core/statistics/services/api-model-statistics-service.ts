// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';

import { ModelIdentifier } from '../../models/models.interface';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { ModelStatisticsDTO } from '../dtos/model-statistics.interface';
import { TrainingModelStatistic, TrainingModelStatisticsGroup } from '../model-statistics.interface';
import { getModelStatisticsEntity } from './utils';

export interface ApiModelStatisticsServiceInterface {
    getModelStatistics: (
        modelIdentifier: ModelIdentifier
    ) => Promise<(TrainingModelStatistic | TrainingModelStatisticsGroup)[]>;
}

export const createApiModelStatisticsService: CreateApiService<ApiModelStatisticsServiceInterface> = (
    { instance, router } = { instance: apiClient, router: API_URLS }
) => {
    return {
        getModelStatistics: async (
            modelIdentifier: ModelIdentifier
        ): Promise<(TrainingModelStatistic | TrainingModelStatisticsGroup)[]> => {
            const { data } = await instance.get<{ model_statistics: ModelStatisticsDTO[] }>(
                router.MODEL_STATISTICS(modelIdentifier)
            );

            const modelStatistics = getModelStatisticsEntity(data.model_statistics);
            const matrixCharts = modelStatistics.filter(({ type }) => type === 'matrix');
            const chartsWithoutMatrix = modelStatistics.filter(({ type }) => type !== 'matrix');

            // Note: matrix always takes two first columns to display, hence we do not want to have row with only
            // one chart and below matrix. For this reason we move matrix charts to be displayed at the end
            return [...chartsWithoutMatrix, ...matrixCharts];
        },
    };
};
