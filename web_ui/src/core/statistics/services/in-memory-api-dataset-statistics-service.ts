// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AllTasksDatasetStatistics, DatasetStatistics, DatasetStatisticsService } from './dataset-statistics.interface';
import { mockedAllDatasetStatistics, mockedDatasetStatistics } from './utils';

export const createInMemoryDatasetStatisticsService = (): DatasetStatisticsService => {
    const getDatasetStatistics = async (): Promise<DatasetStatistics> => mockedDatasetStatistics;

    const getAllTasksDatasetStatistics = async (): Promise<AllTasksDatasetStatistics> => mockedAllDatasetStatistics;

    return { getDatasetStatistics, getAllTasksDatasetStatistics };
};
