// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    InfiniteData,
    QueryKey,
    useInfiniteQuery,
    UseInfiniteQueryResult,
    useMutation,
    UseMutationResult,
    useQuery,
    useQueryClient,
    UseQueryResult,
} from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../../media/media-filter.interface';
import { useModels } from '../../models/hooks/use-models.hook';
import { ProjectIdentifier } from '../../projects/core.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { getErrorMessage } from '../../services/utils';
import { NextPageURL } from '../../shared/infinite-query.interface';
import { TestMediaAdvancedFilter } from '../test-media.interface';
import { Test } from '../tests.interface';
import { isTestJobCompleted } from '../utils';
import { RunTestBody } from './../services/tests-service.interface';

interface UseTests {
    useTestQuery: (projectIdentifier: ProjectIdentifier, testId: string) => UseQueryResult<Test, AxiosError>;
    useTestsListQuery: (projectIdentifier: ProjectIdentifier) => UseQueryResult<Test[], AxiosError>;
    useRunTestMutation: () => UseMutationResult<string, AxiosError, UseRunTestMutation>;
    useMediaItemsOfTestQuery: (
        projectIdentifier: ProjectIdentifier,
        testId: string,
        filterOptions: AdvancedFilterOptions,
        sortingOptions: AdvancedFilterSortingOptions,
        mediaItemsLoadSize?: number
    ) => UseInfiniteQueryResult<InfiniteData<TestMediaAdvancedFilter>, AxiosError>;
    useDeleteTestMutation: () => UseMutationResult<void, AxiosError, DeleteTestParams>;
}

interface UseRunTestMutation {
    projectIdentifier: ProjectIdentifier;
    body: RunTestBody;
}

interface DeleteTestParams {
    projectIdentifier: ProjectIdentifier;
    testId: string;
}

export const useTests = (): UseTests => {
    const { testsService } = useApplicationServices();
    const { addNotification, removeNotifications } = useNotification();
    const queryClient = useQueryClient();

    const onError = (error: AxiosError) => {
        addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
    };

    const useTestsListQuery = (projectIdentifier: ProjectIdentifier): UseQueryResult<Test[], AxiosError> => {
        const { useModelsQuery } = useModels();
        const { data: modelsGroups } = useModelsQuery(projectIdentifier);

        return useQuery<Test[], AxiosError, Test[]>({
            queryKey: QUERY_KEYS.TESTS(projectIdentifier),
            queryFn: () => {
                return testsService.getTests(projectIdentifier, modelsGroups ?? []);
            },
            meta: { notifyOnError: true },
            enabled: !!modelsGroups,
        });
    };

    const useTestQuery = (projectIdentifier: ProjectIdentifier, testId: string): UseQueryResult<Test, AxiosError> => {
        const { useModelsQuery } = useModels();
        const { data: modelsGroups } = useModelsQuery(projectIdentifier);

        return useQuery<Test, AxiosError>({
            queryKey: QUERY_KEYS.TEST(projectIdentifier, testId),
            queryFn: () => {
                return testsService.getTest(projectIdentifier, testId, modelsGroups ?? []);
            },
            meta: { notifyOnError: true },
            enabled: !!modelsGroups,
            // Refetch if the test hasn't completed yet
            refetchInterval: (query) => {
                const test = query.state.data;

                if (test === undefined) {
                    return false;
                }

                if (!isTestJobCompleted(test.jobInfo.status)) {
                    return 10_000;
                }

                return false;
            },
        });
    };

    const useRunTestMutation = (): UseMutationResult<string, AxiosError, UseRunTestMutation> => {
        return useMutation<string, AxiosError, UseRunTestMutation>({
            mutationFn: ({ projectIdentifier, body }: UseRunTestMutation) => {
                return testsService.runTest(projectIdentifier, body);
            },
            onError,
            onSuccess: () => {
                // When user got an error while running test on empty dataset, then user chose correct testing set
                // we want to hide error notification and display custom notification that test has been started
                removeNotifications();
            },
        });
    };

    const useMediaItemsOfTestQuery = (
        projectIdentifier: ProjectIdentifier,
        testId: string,
        filterOptions: AdvancedFilterOptions,
        sortingOptions: AdvancedFilterSortingOptions,
        mediaItemsLoadSize = 50
    ) => {
        return useInfiniteQuery<
            TestMediaAdvancedFilter,
            AxiosError,
            InfiniteData<TestMediaAdvancedFilter>,
            QueryKey,
            NextPageURL
        >({
            queryKey: QUERY_KEYS.TEST_ADVANCED_FILTER_MEDIA(projectIdentifier, testId, filterOptions, sortingOptions),
            queryFn: ({ pageParam: nextPage = null }) => {
                return testsService.getTestMediaAdvancedFilter(
                    projectIdentifier,
                    testId,
                    mediaItemsLoadSize,
                    nextPage,
                    filterOptions,
                    { ...sortingOptions, sortBy: 'score' }
                );
            },
            getNextPageParam: ({ nextPage }) => nextPage,
            getPreviousPageParam: () => undefined,
            meta: { notifyOnError: true },
            initialPageParam: null,
        });
    };

    const useDeleteTestMutation = (): UseMutationResult<void, AxiosError, DeleteTestParams> => {
        return useMutation<void, AxiosError, DeleteTestParams>({
            mutationFn: ({ projectIdentifier, testId }) => {
                return testsService.deleteTest(projectIdentifier, testId);
            },
            onSuccess: async (_, { projectIdentifier }) => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.TESTS(projectIdentifier) });
            },
            onError,
        });
    };

    return {
        useTestsListQuery,
        useRunTestMutation,
        useTestQuery,
        useMediaItemsOfTestQuery,
        useDeleteTestMutation,
    };
};
