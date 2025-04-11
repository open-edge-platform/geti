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
