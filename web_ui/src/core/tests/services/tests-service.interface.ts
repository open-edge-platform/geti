// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../../media/media-filter.interface';
import { ModelsGroups } from '../../models/models.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import { NextPageURL } from '../../shared/infinite-query.interface';
import { TestMediaAdvancedFilter } from '../test-media.interface';
import { MetricType, Test } from '../tests.interface';

export interface RunTestBody {
    name: string;
    modelGroupId: string;
    modelId: string;
    datasetIds: string[];
    metric?: MetricType;
}

export interface TestsService {
    getTests: (projectIdentifier: ProjectIdentifier, modelsGroups: ModelsGroups[]) => Promise<Test[]>;
    runTest: (projectIdentifier: ProjectIdentifier, body: RunTestBody) => Promise<string>;
    getTest: (projectIdentifier: ProjectIdentifier, testId: string, modelsGroups: ModelsGroups[]) => Promise<Test>;
    getTestMediaAdvancedFilter: (
        projectIdentifier: ProjectIdentifier,
        testId: string,
        mediaItemsLoadSize: number,
        nextPageUrl: NextPageURL,
        searchOptions: AdvancedFilterOptions,
        sortingOptions: AdvancedFilterSortingOptions & { sortBy: 'score' }
    ) => Promise<TestMediaAdvancedFilter>;
    deleteTest: (projectIdentifier: ProjectIdentifier, testId: string) => Promise<void>;
}
