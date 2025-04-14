// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
