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

import { ModelIdentifier } from '../../models/models.interface';
import { instance as defaultAxiosInstance } from '../../services/axios-instance';
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
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
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
