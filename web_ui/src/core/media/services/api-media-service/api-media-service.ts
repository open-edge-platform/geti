// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';
import { AxiosProgressEvent, AxiosResponse } from 'axios';

import { CreateApiService } from '../../../../../packages/core/src/services/create-api-service.interface';
import { API_URLS } from '../../../../../packages/core/src/services/urls';
import { DatasetIdentifier } from '../../../projects/dataset.interface';
import { MEDIA_GROUP, MEDIA_TYPE } from '../../base-media.interface';
import {
    ActiveMediaDTO,
    MediaAdvancedFilterDTO,
    MediaAdvancedFramesFilterDTO,
    MediaItemDTO,
} from '../../dtos/media.interface';
import { isImage } from '../../image.interface';
import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../../media-filter.interface';
import {
    MediaAdvancedFilterResponse,
    MediaAdvancedFramesFilterResponse,
    MediaIdentifier,
    MediaItem,
    UploadMediaProps,
} from '../../media.interface';
import { isVideo } from '../../video.interface';
import { GetAdvancedFramesFilterProps, MediaService } from '../media-service.interface';
import { getActiveMediaItems, getMediaFrameFromDTO, getMediaItemFromDTO } from '../utils';

export const createApiMediaService: CreateApiService<MediaService> = (
    { instance, router } = { instance: apiClient, router: API_URLS }
) => {
    const getActiveMedia = async (
        datasetIdentifier: DatasetIdentifier,
        mediaItemsLoadSize: number,
        taskId?: string
    ): Promise<{ media: MediaItem[] }> => {
        const { data, status } = await instance.get<ActiveMediaDTO>(
            router.ACTIVE_MEDIA(datasetIdentifier, mediaItemsLoadSize, taskId)
        );

        if (status === 204) {
            return { media: [] };
        }

        const media = data.active_set.flatMap((item) => {
            return getActiveMediaItems(datasetIdentifier, item, router);
        });

        return { media };
    };

    const getAdvancedFilterMedia = async (
        datasetIdentifier: DatasetIdentifier,
        mediaItemsLoadSize: number,
        nextPageUrl: string | null | undefined,
        searchOptions: AdvancedFilterOptions,
        sortingOptions: AdvancedFilterSortingOptions
    ): Promise<MediaAdvancedFilterResponse> => {
        const loadUrl =
            nextPageUrl ?? router.ADVANCED_DATASET_FILTER(datasetIdentifier, mediaItemsLoadSize, sortingOptions);
        const { data } = await instance.post<MediaAdvancedFilterDTO>(loadUrl, searchOptions);
        const media = data.media.map((item: MediaItemDTO) => getMediaItemFromDTO(datasetIdentifier, item, router));

        return {
            media,
            nextPage: data.next_page,
            totalImages: data.total_images,
            totalMatchedImages: data.total_matched_images,
            totalMatchedVideoFrames: data.total_matched_video_frames,
            totalMatchedVideos: data.total_matched_videos,
            totalVideos: data.total_videos,
        };
    };

    const getAdvancedFramesFilter = async ({
        datasetIdentifier,
        videoId,
        mediaItemsLoadSize,
        nextPage,
        searchOptions,
        sortingOptions,
    }: GetAdvancedFramesFilterProps): Promise<MediaAdvancedFramesFilterResponse> => {
        const loadUrl =
            nextPage ??
            router.ADVANCED_VIDEO_FRAMES_FILTER(datasetIdentifier, videoId, mediaItemsLoadSize, sortingOptions);
        const { data } = await instance.post<MediaAdvancedFramesFilterDTO>(loadUrl, searchOptions);

        return {
            nextPage: data.next_page,
            videoFrames: data.video_frames.map(getMediaFrameFromDTO),
            totalMatchedVideoFrames: data.total_matched_video_frames,
        };
    };

    const getMediaItem = async (
        datasetIdentifier: DatasetIdentifier,
        mediaIdentifier: MediaIdentifier
    ): Promise<MediaItem | undefined> => {
        if (mediaIdentifier.type === MEDIA_TYPE.VIDEO_FRAME) {
            // The API doesn't have a get details endpoint for a video frame, so instead we will
            // get its details from the associated video
            const mediaItem = await getMediaItem(datasetIdentifier, {
                type: MEDIA_TYPE.VIDEO,
                videoId: mediaIdentifier.videoId,
            });

            if (mediaItem === undefined || !isVideo(mediaItem)) {
                throw new Error('Could not retrieve video details for video frame');
            }

            const src = router.MEDIA_ITEM_SRC(datasetIdentifier, mediaIdentifier);

            return { ...mediaItem, identifier: mediaIdentifier, src };
        }

        const loadUrl = router.MEDIA_ITEM(datasetIdentifier, mediaIdentifier);
        const { data } = await instance.get<MediaItemDTO>(loadUrl);

        return getMediaItemFromDTO(datasetIdentifier, data, router);
    };

    const uploadMedia = (uploadMediaProps: UploadMediaProps): Promise<AxiosResponse<MediaItemDTO>> => {
        const { media } = uploadMediaProps;
        const mediaGroup = media.file.type.startsWith(MEDIA_TYPE.IMAGE) ? MEDIA_GROUP.IMAGES : MEDIA_GROUP.VIDEOS;

        return uploadMediaFile(uploadMediaProps, mediaGroup);
    };

    const deleteMedia = (datasetIdentifier: DatasetIdentifier, mediaItem: MediaItem): Promise<void> => {
        const { mediaItemId, mediaGroup } = isImage(mediaItem)
            ? { mediaItemId: mediaItem.identifier.imageId, mediaGroup: MEDIA_GROUP.IMAGES }
            : { mediaItemId: mediaItem.identifier.videoId, mediaGroup: MEDIA_GROUP.VIDEOS };

        return deleteMediaFile(datasetIdentifier, mediaItemId, mediaGroup);
    };

    const uploadMediaFile = (
        uploadMediaProps: UploadMediaProps,
        mediaGroup: MEDIA_GROUP
    ): Promise<AxiosResponse<MediaItemDTO>> => {
        const { datasetIdentifier, uploadId, media, onProgress, abortController } = uploadMediaProps;

        const { file, uploadInfo, meta } = media;
        const formData = new FormData();

        formData.set('file', file);

        if (uploadInfo) formData.set('upload_info', JSON.stringify(uploadInfo));

        return instance.post<MediaItemDTO>(router.MEDIA_UPLOAD(datasetIdentifier, mediaGroup), formData, {
            signal: abortController.signal,
            headers: { 'content-type': 'multipart/form-data' },
            onUploadProgress: (event: AxiosProgressEvent) => {
                onProgress({
                    uploadId,
                    datasetIdentifier,
                    file,
                    fileName: file.name,
                    fileSize: file.size,
                    fileType: file.type,
                    progress: event.total ? Math.round((event.loaded * 100) / event.total) : 0,
                    meta,
                });
            },
        });
    };

    const deleteMediaFile = (
        datasetIdentifier: DatasetIdentifier,
        mediaItemId: string,
        mediaGroup: MEDIA_GROUP
    ): Promise<void> => {
        return instance.delete(router.MEDIA_DELETE(datasetIdentifier, mediaGroup, mediaItemId));
    };

    return { getMediaItem, getActiveMedia, uploadMedia, deleteMedia, getAdvancedFilterMedia, getAdvancedFramesFilter };
};
