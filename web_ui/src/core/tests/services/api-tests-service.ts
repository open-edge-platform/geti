// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';
import { orderBy } from 'lodash-es';

import { mapSearchRulesToDto } from '../../datasets/services/utils';
import { JobTestDTO } from '../../jobs/dtos/jobs-dto.interface';
import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../../media/media-filter.interface';
import { ModelsGroups } from '../../models/models.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { TestMediaAdvancedFilterDTO } from '../dtos/test-media.interface';
import { TestDTO, TestsDTO } from '../dtos/tests.interface';
import { TestMediaAdvancedFilter } from '../test-media.interface';
import { Test } from '../tests.interface';
import { RunTestBody, TestsService } from './tests-service.interface';
import { getRunTestBodyDTO, getTestEntity, getTestMediaItemEntity } from './utils';

export const createApiTestsService: CreateApiService<TestsService> = (
    { instance, router } = { instance: apiClient, router: API_URLS }
) => {
    const getTests = async (projectIdentifier: ProjectIdentifier, modelsGroups: ModelsGroups[]): Promise<Test[]> => {
        const { data } = await instance.get<TestsDTO>(router.TESTS(projectIdentifier));

        const tests = data.test_results.map((test) => {
            return getTestEntity(test, modelsGroups);
        });

        return orderBy(tests, 'creationTime', 'desc');
    };

    const runTest = async (projectIdentifier: ProjectIdentifier, body: RunTestBody): Promise<string> => {
        const { data } = await instance.post<JobTestDTO>(router.TESTS(projectIdentifier), getRunTestBodyDTO(body));

        return data.id;
    };

    const getTest = async (
        projectIdentifier: ProjectIdentifier,
        testId: string,
        modelsGroups: ModelsGroups[]
    ): Promise<Test> => {
        const { data } = await instance.get<TestDTO>(router.TEST(projectIdentifier, testId));

        return getTestEntity(data, modelsGroups);
    };

    const getTestMediaAdvancedFilter = async (
        projectIdentifier: ProjectIdentifier,
        testId: string,
        mediaItemsLoadSize: number,
        nextPageUrl: string | null | undefined,
        searchOptions: AdvancedFilterOptions,
        sortingOptions: AdvancedFilterSortingOptions & { sortBy: 'score' }
    ): Promise<TestMediaAdvancedFilter> => {
        const url =
            nextPageUrl ?? router.TEST_MEDIA_FILTER(projectIdentifier, testId, mediaItemsLoadSize, sortingOptions);

        const { data } = await instance.post<TestMediaAdvancedFilterDTO>(url, {
            rules: mapSearchRulesToDto(searchOptions.rules),
            condition: searchOptions.condition,
        });
        const {
            next_page,
            media,
            total_images,
            total_matched_images,
            total_matched_video_frames,
            total_matched_videos,
            total_videos,
        } = data;

        return {
            nextPage: next_page,
            media: media.map(getTestMediaItemEntity),
            totalImages: total_images,
            totalVideos: total_videos,
            totalMatchedImages: total_matched_images,
            totalMatchedVideos: total_matched_videos,
            totalMatchedVideoFrames: total_matched_video_frames,
        };
    };

    const deleteTest = async (projectIdentifier: ProjectIdentifier, testId: string): Promise<void> => {
        await instance.delete(router.TEST(projectIdentifier, testId));
    };

    return {
        getTests,
        runTest,
        getTest,
        deleteTest,
        getTestMediaAdvancedFilter,
    };
};
