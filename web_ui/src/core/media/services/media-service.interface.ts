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

import { AxiosResponse } from 'axios';

import { DatasetIdentifier } from '../../projects/dataset.interface';
import { NextPageURL } from '../../shared/infinite-query.interface';
import { MediaItemDTO } from '../dtos/media.interface';
import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../media-filter.interface';
import {
    MediaAdvancedFilterResponse,
    MediaAdvancedFramesFilterResponse,
    MediaIdentifier,
    MediaItem,
    UploadMediaProps,
} from '../media.interface';

export interface GetAdvancedFramesFilterProps {
    videoId: string;
    mediaItemsLoadSize: number;
    datasetIdentifier: DatasetIdentifier;
    nextPage: NextPageURL;
    searchOptions: AdvancedFilterOptions;
    sortingOptions: AdvancedFilterSortingOptions;
}

export interface MediaService {
    getAdvancedFilterMedia(
        { workspaceId, projectId, datasetId, organizationId }: DatasetIdentifier,
        mediaItemsLoadSize: number,
        nextPageUrl: NextPageURL,
        searchOptions: AdvancedFilterOptions,
        sortingOptions: AdvancedFilterSortingOptions
    ): Promise<MediaAdvancedFilterResponse>;

    getAdvancedFramesFilter(data: GetAdvancedFramesFilterProps): Promise<MediaAdvancedFramesFilterResponse>;

    getActiveMedia(
        datasetIdentifier: DatasetIdentifier,
        mediaItemsLoadSize: number,
        taskId?: string
    ): Promise<{ media: MediaItem[] }>;

    getMediaItem(
        datasetIdentifier: DatasetIdentifier,
        mediaIdentifier: MediaIdentifier
    ): Promise<MediaItem | undefined>;

    uploadMedia(uploadMediaProps: UploadMediaProps): Promise<AxiosResponse<MediaItemDTO>>;
    deleteMedia(datasetIdentifier: DatasetIdentifier, mediaItem: MediaItem): Promise<void>;
}
