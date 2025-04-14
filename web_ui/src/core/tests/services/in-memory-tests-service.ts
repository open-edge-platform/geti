// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../../media/media-filter.interface';
import { ModelsGroups } from '../../models/models.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import { TestMediaAdvancedFilter } from '../test-media.interface';
import { Test } from '../tests.interface';
import { RunTestBody, TestsService } from './tests-service.interface';
import { getMockedTest, getMockedTestImageMediaItem } from './tests-utils';

export const createInMemoryTestsService = (): TestsService => {
    const getTests = async (_projectIdentifier: ProjectIdentifier, _modelsGroups: ModelsGroups[]): Promise<Test[]> => {
        return Promise.resolve([
            getMockedTest({ id: 'test-1', testName: 'Test 1' }),
            getMockedTest({ id: 'test-2', testName: 'Test 2' }),
        ]);
    };

    const getTest = async (
        _projectIdentifier: ProjectIdentifier,
        _testId: string,
        _modelsGroups: ModelsGroups[]
    ): Promise<Test> => {
        return Promise.resolve(getMockedTest());
    };

    const runTest = async (_projectIdentifier: ProjectIdentifier, _body: RunTestBody): Promise<string> => {
        return Promise.resolve('id');
    };

    const getTestMediaAdvancedFilter = async (
        _projectIdentifier: ProjectIdentifier,
        _testId: string,
        _mediaItemsLoadSize: number,
        _nextPageUrl: string | null | undefined,
        _searchOptions: AdvancedFilterOptions,
        _sortingOptions: AdvancedFilterSortingOptions & { sortBy: 'score' }
    ): Promise<TestMediaAdvancedFilter> => {
        return Promise.resolve({
            media: [getMockedTestImageMediaItem()],
            nextPage: undefined,
            totalImages: 3,
            totalVideos: 2,
            totalMatchedImages: 1,
            totalMatchedVideos: 1,
            totalMatchedVideoFrames: 1,
        });
    };

    const deleteTest = (_projectIdentifier: ProjectIdentifier, _testId: string): Promise<void> => {
        return Promise.resolve();
    };

    return {
        getTests,
        runTest,
        getTest,
        deleteTest,
        getTestMediaAdvancedFilter,
    };
};
