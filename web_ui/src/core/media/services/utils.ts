// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { sortBy } from 'lodash-es';

import { API_URLS } from '../../../../packages/core/src/services/urls';
import { ImageIdDTO, VideoFrameIdDTO, VideoIdDTO } from '../../annotations/dtos/annotation.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import { DatasetIdentifier } from '../../projects/dataset.interface';
import { MEDIA_TYPE } from '../base-media.interface';
import { AnnotationStatePerTask } from '../base.interface';
import { AnnotationStatePerTaskDTO } from '../dtos/base.interface';
import { ActiveMediaItemDTO, MediaItemDTO } from '../dtos/media.interface';
import { FilterVideoFrameMediaDTO, VideoFrameMediaDTO, VideoStatisticsDTO } from '../dtos/video.interface';
import { MediaIdentifier, MediaItem } from '../media.interface';
import { FilterVideoFrame, isVideo, isVideoFrame, VideoStatistics } from '../video.interface';

export const mediaIdentifierToDTO = (mediaIdentifier: MediaIdentifier): ImageIdDTO | VideoIdDTO | VideoFrameIdDTO => {
    if (mediaIdentifier.type === MEDIA_TYPE.IMAGE) {
        return {
            type: 'image',
            image_id: mediaIdentifier.imageId,
        };
    }

    const identifier = { identifier: mediaIdentifier };

    if (isVideoFrame(identifier)) {
        return {
            type: 'video_frame',
            video_id: mediaIdentifier.videoId,
            frame_index: identifier.identifier.frameNumber,
        };
    }

    return {
        type: 'video',
        video_id: mediaIdentifier.videoId,
    };
};

export const getAnnotationStatePerTaskFromDTO = (
    annotationStatePerTask: AnnotationStatePerTaskDTO[]
): AnnotationStatePerTask[] =>
    annotationStatePerTask?.map(({ task_id, state }) => ({
        taskId: task_id,
        state,
    }));

const getAnnotationStatisticsFromDTO = (statisticsDTO: VideoStatisticsDTO): VideoStatistics => ({
    annotated: statisticsDTO.annotated,
    partiallyAnnotated: statisticsDTO.partially_annotated,
    unannotated: statisticsDTO.unannotated,
});

export const getMediaItemFromDTO = (
    datasetIdentifier: DatasetIdentifier,
    item: MediaItemDTO | VideoFrameMediaDTO,
    router = API_URLS
): MediaItem => {
    const {
        id,
        state,
        name,
        annotation_scene_id,
        annotation_state_per_task,
        media_information,
        upload_time,
        uploader_id,
        last_annotator_id,
    } = item;
    const { size, height, width } = media_information;

    const baseMediaItem = {
        name,
        status: state,
        annotationSceneId: annotation_scene_id,
        metadata: {
            width,
            height,
            size,
        },
        uploadTime: upload_time,
        uploaderId: uploader_id,
        annotationStatePerTask: getAnnotationStatePerTaskFromDTO(annotation_state_per_task),
        lastAnnotatorId: last_annotator_id,
    };

    switch (item.type) {
        case MEDIA_TYPE.IMAGE: {
            const identifier = { type: MEDIA_TYPE.IMAGE as const, imageId: id };
            const src = router.MEDIA_ITEM_SRC(datasetIdentifier, identifier);
            const thumbnailSrc = router.MEDIA_ITEM_THUMBNAIL(datasetIdentifier, identifier);

            return { ...baseMediaItem, identifier, src, thumbnailSrc };
        }
        case MEDIA_TYPE.VIDEO: {
            const identifier = { type: MEDIA_TYPE.VIDEO as const, videoId: id };
            const src = router.MEDIA_ITEM_STREAM(datasetIdentifier, identifier);
            const thumbnailSrc = router.MEDIA_ITEM_THUMBNAIL(datasetIdentifier, identifier);
            const { duration, frame_count: frames, frame_stride: frameStride } = item.media_information;
            const fps = item.media_information.frame_rate;
            const metadata = { ...baseMediaItem.metadata, fps, frames, duration, frameStride };

            return {
                ...baseMediaItem,
                identifier,
                metadata,
                src,
                thumbnailSrc,
                matchedFrames: item.matched_frames,
                annotationStatistics: item.annotation_statistics
                    ? getAnnotationStatisticsFromDTO(item.annotation_statistics)
                    : undefined,
            };
        }
        case MEDIA_TYPE.VIDEO_FRAME: {
            const frameNumber = Number('id' in item ? item.id : (item as VideoFrameMediaDTO).frame_index);
            const {
                duration,
                frame_count: frames,
                frame_stride: frameStride,
                video_id: videoId,
            } = item.media_information;
            const identifier: MediaIdentifier = { type: MEDIA_TYPE.VIDEO_FRAME as const, videoId, frameNumber };
            const src = router.MEDIA_ITEM_SRC(datasetIdentifier, identifier);
            const thumbnailSrc = router.MEDIA_ITEM_THUMBNAIL(datasetIdentifier, identifier);
            const fps = item.media_information.frame_rate;
            const metadata = { ...baseMediaItem.metadata, fps, frames, duration, frameStride };

            return { ...baseMediaItem, identifier, metadata, src, thumbnailSrc };
        }
        default: {
            throw new Error(`Unsupported media type`);
        }
    }
};

export const getMediaFrameFromDTO = (frame: FilterVideoFrameMediaDTO): FilterVideoFrame => {
    return {
        identifier: {
            type: MEDIA_TYPE.VIDEO_FRAME,
            videoId: frame.video_id,
            frameNumber: frame.frame_index,
        },
        name: frame.name,
        src: frame.media_information.display_url,
        thumbnailSrc: frame.thumbnail,
        uploadTime: frame.upload_time,
        uploaderId: frame.uploader_id,
        annotationStatePerTask: frame.annotation_state_per_task,
        metadata: {
            height: frame.media_information.height,
            width: frame.media_information.width,
        },
    };
};

const determineDatasetIdFromSrc = (src: string) => {
    const regex = /.*datasets\/(.*)\/media.*/;
    const match = src.match(regex);

    if (match === null) {
        throw new Error('Could not determine dataset id based on thumbnail src');
    }

    return match[1];
};

export const getActiveMediaItems = (
    projectIdentifier: ProjectIdentifier,
    item: ActiveMediaItemDTO,
    router = API_URLS
): MediaItem[] => {
    // NOTE: currently we don't receive the dataset id from the server side,
    // so we need to determine it from the provided thumbnail
    // This should be replaced by the dataset id returned from the server
    // once they support this
    const datasetId = determineDatasetIdFromSrc(item.thumbnail);
    const datasetIdentifier = { ...projectIdentifier, datasetId };

    if (item.type === 'image') {
        return [getMediaItemFromDTO(datasetIdentifier, item)];
    }

    if (item.type === 'video') {
        const videoMediaItem = getMediaItemFromDTO(datasetIdentifier, item);

        if (!isVideo(videoMediaItem) && !isVideoFrame(videoMediaItem)) {
            throw new Error('Expected to receive video');
        }

        const videoFrames = item.active_frames.map((frameNumber) => {
            const identifier = {
                type: MEDIA_TYPE.VIDEO_FRAME,
                videoId: item.id,
                frameNumber,
            } as const;
            const src = router.MEDIA_ITEM_SRC(datasetIdentifier, identifier);
            const thumbnailSrc = router.MEDIA_ITEM_THUMBNAIL(datasetIdentifier, identifier);

            return {
                name: item.name,
                identifier,
                src,
                thumbnailSrc,
                status: item.state,
                metadata: videoMediaItem.metadata,
                annotationStatePerTask: getAnnotationStatePerTaskFromDTO(item.annotation_state_per_task),
                annotationStatistics: item.annotation_statistics
                    ? getAnnotationStatisticsFromDTO(item.annotation_statistics)
                    : undefined,
                uploadTime: videoMediaItem.uploadTime,
                uploaderId: videoMediaItem.uploaderId,
                lastAnnotatorId: videoMediaItem.lastAnnotatorId,
            };
        });

        return sortBy(videoFrames, (videoFrame) => {
            return videoFrame.identifier.frameNumber;
        });
    }

    throw new Error(`Received an unsupported media type`);
};
