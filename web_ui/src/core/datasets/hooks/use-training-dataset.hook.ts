// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { InfiniteData, QueryKey, useInfiniteQuery, useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../../media/media-filter.interface';
import { MediaAdvancedFilterResponse } from '../../media/media.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { NextPageURL } from '../../shared/infinite-query.interface';
import { TrainingDatasetRevision } from '../services/training-dataset.interface';

export const useTrainingDatasetRevisionData = (
    projectIdentifier: ProjectIdentifier,
    storageId: string,
    revisionId: string
): UseQueryResult<TrainingDatasetRevision, AxiosError> => {
    const { trainingDatasetService } = useApplicationServices();

    return useQuery({
        queryKey: QUERY_KEYS.TRAINING_DATASET_REVISION_KEY(projectIdentifier, storageId, revisionId),
        queryFn: () => {
            return trainingDatasetService.getTrainingDatasetRevision(projectIdentifier, storageId, revisionId);
        },
        meta: { notifyOnError: true },
    });
};

export const useTrainingDatasetMediaQuery = (
    projectIdentifier: ProjectIdentifier,
    datasetStorageId: string,
    datasetRevisionId: string,
    searchOptions: AdvancedFilterOptions,
    sortingOptions: AdvancedFilterSortingOptions,
    mediaItemsLoadSize = 50
) => {
    const { trainingDatasetService } = useApplicationServices();

    return useInfiniteQuery<
        MediaAdvancedFilterResponse,
        AxiosError,
        InfiniteData<MediaAdvancedFilterResponse>,
        QueryKey,
        NextPageURL
    >({
        queryKey: QUERY_KEYS.TRAINING_DATASET_ADVANCED_FILTER_MEDIA(
            projectIdentifier,
            datasetStorageId,
            datasetRevisionId,
            searchOptions,
            sortingOptions
        ),
        queryFn: ({ pageParam: nextPage = null }) => {
            return trainingDatasetService.getTrainingDatasetMediaAdvancedFilter(
                projectIdentifier,
                datasetStorageId,
                datasetRevisionId,
                mediaItemsLoadSize,
                nextPage,
                searchOptions,
                sortingOptions
            );
        },
        getNextPageParam: ({ nextPage }) => nextPage,
        getPreviousPageParam: () => undefined,
        meta: { notifyOnError: true },
        initialPageParam: null,
    });
};

export const useTrainingDatasetVideo = (
    projectIdentifier: ProjectIdentifier,
    datasetStorageId: string,
    datasetRevisionId: string,
    videoId: string,
    searchOptions: AdvancedFilterOptions,
    sortingOptions: AdvancedFilterSortingOptions,
    mediaItemsLoadSize = 50
) => {
    const { trainingDatasetService } = useApplicationServices();

    return useQuery({
        queryKey: QUERY_KEYS.TRAINING_DATASET_ADVANCED_FILTER_VIDEO(
            projectIdentifier,
            datasetStorageId,
            datasetRevisionId,
            videoId,
            searchOptions,
            sortingOptions
        ),
        queryFn: () => {
            return trainingDatasetService.getVideoTrainingDatasetAdvancedFilter(
                projectIdentifier,
                datasetStorageId,
                datasetRevisionId,
                videoId,
                mediaItemsLoadSize,
                null,
                searchOptions,
                sortingOptions
            );
        },
        meta: { notifyOnError: true },
    });
};
