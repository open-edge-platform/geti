// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MediaAdvancedFilterDTO, MediaItemDTO } from '../../media/dtos/media.interface';
import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../../media/media-filter.interface';
import { MediaAdvancedFilterResponse } from '../../media/media.interface';
import { getMediaItemFromDTO } from '../../media/services/utils';
import { VideoFrame } from '../../media/video.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { NextPageURL } from '../../shared/infinite-query.interface';
import { TrainingDatasetDTO } from '../dtos/training-dataset.interface';
import { TrainingDatasetRevision, TrainingDatasetRevisionVideo } from './training-dataset.interface';
import { getTrainingDatasetRevisionData, mapSearchRulesToDto } from './utils';

export interface TrainingDatasetService {
    getTrainingDatasetRevision: (
        projectIdentifier: ProjectIdentifier,
        datasetId: string,
        revisionId: string
    ) => Promise<TrainingDatasetRevision>;
    getTrainingDatasetMediaAdvancedFilter: (
        projectIdentifier: ProjectIdentifier,
        datasetStorageId: string,
        datasetRevisionId: string,
        mediaItemsLoadSize: number,
        nextPageUrl: NextPageURL,
        searchOptions: AdvancedFilterOptions,
        sortingOptions: AdvancedFilterSortingOptions
    ) => Promise<MediaAdvancedFilterResponse>;

    getVideoTrainingDatasetAdvancedFilter: (
        projectIdentifier: ProjectIdentifier,
        datasetStorageId: string,
        datasetRevisionId: string,
        videoId: string,
        mediaItemsLoadSize: number,
        nextPageUrl: NextPageURL,
        searchOptions: AdvancedFilterOptions,
        sortingOptions: AdvancedFilterSortingOptions
    ) => Promise<TrainingDatasetRevisionVideo>;
}

export const createApiTrainingDatasetService: CreateApiService<TrainingDatasetService> = (
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
) => {
    const getTrainingDatasetRevision = async (
        projectIdentifier: ProjectIdentifier,
        datasetId: string,
        revisionId: string
    ): Promise<TrainingDatasetRevision> => {
        const { data } = await instance.get<TrainingDatasetDTO>(
            router.TRAINING_REVISION_URL(projectIdentifier, datasetId, revisionId)
        );

        return getTrainingDatasetRevisionData(data);
    };

    const getVideoTrainingDatasetAdvancedFilter = async (
        projectIdentifier: ProjectIdentifier,
        datasetStorageId: string,
        datasetRevisionId: string,
        videoId: string,
        mediaItemsLoadSize: number,
        nextPageUrl: string | null | undefined,
        searchOptions: AdvancedFilterOptions,
        sortingOptions: AdvancedFilterSortingOptions
    ): Promise<TrainingDatasetRevisionVideo> => {
        const url =
            nextPageUrl ??
            router.VIDEO_TRAINING_ADVANCED_DATASET_FILTER(
                projectIdentifier,
                datasetStorageId,
                datasetRevisionId,
                videoId,
                mediaItemsLoadSize,
                sortingOptions
            );

        const { data } = await instance.post<MediaAdvancedFilterDTO>(url, {
            rules: mapSearchRulesToDto(searchOptions.rules),
            condition: searchOptions.condition,
        });

        const { media, total_matched_video_frames } = data;

        return {
            frames: media.map((item: MediaItemDTO) => {
                return getMediaItemFromDTO({ ...projectIdentifier, datasetId: datasetStorageId }, item) as VideoFrame;
            }),
            matchedFrames: total_matched_video_frames,
        };
    };

    const getTrainingDatasetMediaAdvancedFilter = async (
        projectIdentifier: ProjectIdentifier,
        datasetStorageId: string,
        datasetRevisionId: string,
        mediaItemsLoadSize: number,
        nextPageUrl: string | null | undefined,
        searchOptions: AdvancedFilterOptions,
        sortingOptions: AdvancedFilterSortingOptions
    ): Promise<MediaAdvancedFilterResponse> => {
        const url =
            nextPageUrl ??
            router.TRAINING_ADVANCED_DATASET_FILTER(
                projectIdentifier,
                datasetStorageId,
                datasetRevisionId,
                mediaItemsLoadSize,
                sortingOptions
            );

        const { data } = await instance.post<MediaAdvancedFilterDTO>(url, {
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
            media: media.map((item: MediaItemDTO) => {
                return getMediaItemFromDTO({ ...projectIdentifier, datasetId: datasetStorageId }, item);
            }),
            totalImages: total_images,
            totalVideos: total_videos,
            totalMatchedImages: total_matched_images,
            totalMatchedVideos: total_matched_videos,
            totalMatchedVideoFrames: total_matched_video_frames,
        };
    };

    return {
        getTrainingDatasetRevision,
        getTrainingDatasetMediaAdvancedFilter,
        getVideoTrainingDatasetAdvancedFilter,
    };
};
