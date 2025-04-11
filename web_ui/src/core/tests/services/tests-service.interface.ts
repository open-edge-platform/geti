// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
