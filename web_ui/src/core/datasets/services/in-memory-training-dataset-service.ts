// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../../media/media-filter.interface';
import { MediaAdvancedFilterResponse } from '../../media/media.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import { TrainingDatasetService } from './api-training-dataset-service';
import { TrainingDatasetRevision, TrainingDatasetRevisionVideo } from './training-dataset.interface';

export const createInMemoryTrainingDatasetService = (): TrainingDatasetService => {
    const getTrainingDatasetRevision = async (
        _projectIdentifier: ProjectIdentifier,
        _datasetId: string,
        _revisionId: string
    ): Promise<TrainingDatasetRevision> => {
        return {
            id: 'in-memory-training-dataset-test-id',
            trainingSubset: 50,
            validationSubset: 23,
            testingSubset: 45,
        };
    };

    const getTrainingDatasetMediaAdvancedFilter = async (
        _projectIdentifier: ProjectIdentifier,
        _datasetStorageId: string,
        _datasetRevisionId: string,
        _mediaItemsLoadSize: number,
        _nextPageUrl: string | null | undefined,
        _searchOptions: AdvancedFilterOptions,
        _sortingOptions: AdvancedFilterSortingOptions
    ): Promise<MediaAdvancedFilterResponse> => {
        return Promise.resolve({
            media: [],
            nextPage: undefined,
            totalImages: 3,
            totalVideos: 2,
            totalMatchedImages: 1,
            totalMatchedVideos: 1,
            totalMatchedVideoFrames: 1,
        });
    };

    const getVideoTrainingDatasetAdvancedFilter = async (
        _projectIdentifier: ProjectIdentifier,
        _datasetStorageId: string,
        _datasetRevisionId: string,
        _videoId: string,
        _mediaItemsLoadSize: number,
        _nextPageUrl: string | null | undefined,
        _searchOptions: AdvancedFilterOptions,
        _sortingOptions: AdvancedFilterSortingOptions
    ): Promise<TrainingDatasetRevisionVideo> => {
        return Promise.resolve({
            frames: [],
            matchedFrames: 0,
        });
    };

    return {
        getTrainingDatasetRevision,
        getTrainingDatasetMediaAdvancedFilter,
        getVideoTrainingDatasetAdvancedFilter,
    };
};
