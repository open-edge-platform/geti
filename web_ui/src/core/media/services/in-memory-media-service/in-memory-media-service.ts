// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

/* eslint-disable @typescript-eslint/no-unused-vars */

import { AxiosResponse } from 'axios';
import isEqual from 'lodash/isEqual';

import { DatasetIdentifier } from '../../../projects/dataset.interface';
import { MediaItemDTO } from '../../dtos/media.interface';
import {
    MediaAdvancedFilterResponse,
    MediaAdvancedFramesFilterResponse,
    MediaIdentifier,
    MediaItem,
    MediaItemResponse,
    UploadMediaProps,
} from '../../media.interface';
import { GetAdvancedFramesFilterProps, MediaService } from '../media-service.interface';
import { DEFAULT_IN_MEMORY_MEDIA } from './default-media';

export const createInMemoryMediaService = (defaultMedia: MediaItem[] = DEFAULT_IN_MEMORY_MEDIA): MediaService => {
    const getMedia = async (_datasetIdentifier: DatasetIdentifier): Promise<MediaItemResponse> => {
        return {
            nextPage: undefined,
            media: defaultMedia,
            mediaCount: { images: 10, videos: 10 },
        };
    };

    const getAdvancedFilterMedia = async (
        _datasetIdentifier: DatasetIdentifier
    ): Promise<MediaAdvancedFilterResponse> => {
        return {
            nextPage: undefined,
            media: defaultMedia,
            totalImages: 10,
            totalMatchedImages: 10,
            totalMatchedVideoFrames: 10,
            totalMatchedVideos: 10,
            totalVideos: 10,
        };
    };

    const getAdvancedFramesFilter = async (
        _data: GetAdvancedFramesFilterProps
    ): Promise<MediaAdvancedFramesFilterResponse> => {
        return {
            nextPage: undefined,
            videoFrames: [],
            totalMatchedVideoFrames: 10,
        };
    };

    const getActiveMedia = async (
        datasetIdentifier: DatasetIdentifier,
        _mediaItemsLoadSize: number
    ): Promise<{ media: MediaItem[] }> => {
        return getMedia(datasetIdentifier);
    };

    const uploadMedia = (uploadMediaProps: UploadMediaProps): Promise<AxiosResponse<MediaItemDTO>> => {
        return new Promise<AxiosResponse<MediaItemDTO>>(() => undefined);
    };

    const deleteMedia = (_datasetIdentifier: DatasetIdentifier, _mediaItem: MediaItem): Promise<void> => {
        return Promise.resolve(undefined);
    };

    const getMediaItem = async (
        datasetIdentifier: DatasetIdentifier,
        mediaIdentifier: MediaIdentifier
    ): Promise<MediaItem | undefined> => {
        const { media } = await getMedia(datasetIdentifier);
        return media.find((mediaItem) => {
            return isEqual(mediaItem.identifier, mediaIdentifier);
        });
    };

    return { getMediaItem, getActiveMedia, uploadMedia, deleteMedia, getAdvancedFilterMedia, getAdvancedFramesFilter };
};
