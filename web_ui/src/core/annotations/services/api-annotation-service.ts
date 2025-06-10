// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';
import { HttpStatusCode, isAxiosError } from 'axios';

import { CreateApiService } from '../../../../packages/core/src/services/create-api-service.interface';
import { API_URLS } from '../../../../packages/core/src/services/urls';
import { getIds } from '../../../shared/utils';
import { Label } from '../../labels/label.interface';
import { MediaItem } from '../../media/media.interface';
import { mediaIdentifierToDTO } from '../../media/services/utils';
import { Video } from '../../media/video.interface';
import { DatasetIdentifier } from '../../projects/dataset.interface';
import { Annotation } from '../annotation.interface';
import {
    AnnotationResultDTO,
    RangeAnnotationDTO,
    RangeAnnotationResponseDTO,
    VideoAnnotationsDTO,
} from '../dtos/annotation.interface';
import { LabeledVideoRange } from '../labeled-video-range.interface';
import { AnnotationService } from './annotation-service.interface';
import { getAnnotationsFromDTO, getKeypointToAnnotationDTO, isKeypointAnnotation, toAnnotationDTO } from './utils';
import { VideoPaginationOptions } from './video-pagination-options.interface';

export const createApiAnnotationService: CreateApiService<AnnotationService> = (
    { instance, router } = { instance: apiClient, router: API_URLS }
) => {
    const getAnnotations = async (
        datasetIdentifier: DatasetIdentifier,
        projectLabels: Label[],
        mediaItem: MediaItem,
        annotationId = 'latest'
    ): Promise<Annotation[]> => {
        try {
            const { data } = await instance.get<AnnotationResultDTO>(
                router.ANNOTATIONS(datasetIdentifier, mediaItem.identifier, annotationId)
            );

            if (!data) {
                return [];
            }

            return getAnnotationsFromDTO(data.annotations, projectLabels);
        } catch (error) {
            if (isAxiosError(error) && error.response?.status === HttpStatusCode.NotFound) {
                return [];
            }

            throw error;
        }
    };

    const getVideoAnnotations = async (
        datasetIdentifier: DatasetIdentifier,
        projectLabels: Label[],
        mediaItem: Video,
        options: VideoPaginationOptions = {
            startFrame: 0,
            endFrame: mediaItem.metadata.frames,
            frameSkip: mediaItem.metadata.frameStride,
            labelsOnly: false,
        }
    ) => {
        // Currently the UI does not fully support paginated responses for a video's annotations,
        // therefore we try to fetch all pages in this method
        const annotationsByFrameNumber: Record<number, Annotation[]> = {};
        let getMorePages = true;

        while (getMorePages) {
            const url = router.ANNOTATIONS(datasetIdentifier, mediaItem.identifier, undefined, options);

            const { data } = await instance.get<VideoAnnotationsDTO>(url);

            if (!data) {
                break;
            }

            if (data.video_annotation_properties.total_requested_count > data.video_annotation_properties.total_count) {
                options.startFrame = data.video_annotation_properties.end_frame + 1;
                getMorePages = true;
            } else {
                getMorePages = false;
            }

            // Make sure that we escape the loop if we receive weird data
            if (
                isNaN(data.video_annotation_properties.total_requested_count) ||
                isNaN(data.video_annotation_properties.total_count) ||
                data.video_annotation_properties.total_requested_count < 0 ||
                data.video_annotation_properties.total_count < 0
            ) {
                getMorePages = false;
            }

            data.video_annotations.forEach((media) => {
                const annotations = getAnnotationsFromDTO(media.annotations, projectLabels);

                annotationsByFrameNumber[media.media_identifier.frame_index] = annotations;
            });
        }

        return annotationsByFrameNumber;
    };

    const saveAnnotations = async (
        datasetIdentifier: DatasetIdentifier,
        mediaItem: MediaItem,
        annotations: Annotation[]
    ): Promise<AnnotationResultDTO> => {
        const annotationsDTO = annotations.flatMap((annotation) => {
            if (isKeypointAnnotation(annotation)) {
                return getKeypointToAnnotationDTO(annotation);
            }
            return toAnnotationDTO(annotation);
        });

        const data = {
            media_identifier: mediaIdentifierToDTO(mediaItem.identifier),
            annotations: annotationsDTO,
        };
        const annotationResult = await instance.post(
            router.SAVE_ANNOTATIONS(datasetIdentifier, mediaItem.identifier),
            data
        );

        return annotationResult.data;
    };

    const getLabeledVideoRanges = async (
        datasetIdentifier: DatasetIdentifier,
        mediaItem: Video,
        projectLabels: Label[]
    ): Promise<LabeledVideoRange[]> => {
        const { data } = await instance.get<RangeAnnotationResponseDTO>(
            router.RANGE_ANNOTATIONS(datasetIdentifier, mediaItem.identifier)
        );

        return data.range_labels.map(({ label_ids, end_frame, start_frame }) => ({
            labels: projectLabels.filter((projectLabel) => label_ids.includes(projectLabel.id)),
            start: start_frame,
            end: end_frame,
        }));
    };

    const saveLabeledVideoRanges = async (
        datasetIdentifier: DatasetIdentifier,
        mediaItem: Video,
        ranges: LabeledVideoRange[]
    ): Promise<void> => {
        const data = {
            range_labels: ranges.map((range) => {
                return {
                    start_frame: range.start,
                    end_frame: range.end,
                    label_ids: getIds(range.labels),
                };
            }),
        };

        await instance.post<RangeAnnotationDTO>(
            router.RANGE_ANNOTATIONS(datasetIdentifier, mediaItem.identifier),
            data
        );
    };

    return {
        getAnnotations,
        getVideoAnnotations,
        saveAnnotations,
        getLabeledVideoRanges,
        saveLabeledVideoRanges,
    };
};
