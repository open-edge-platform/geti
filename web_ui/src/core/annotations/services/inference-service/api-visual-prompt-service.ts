// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';

import { Label } from '../../../labels/label.interface';
import { MediaItem } from '../../../media/media.interface';
import { mediaIdentifierToDTO } from '../../../media/services/utils';
import { isVideo } from '../../../media/video.interface';
import { DatasetIdentifier } from '../../../projects/dataset.interface';
import { API_URLS } from '../../../services/urls';
import { ImageIdDTO, VideoFrameIdDTO } from '../../dtos/annotation.interface';
import { NewPredictionsDTO } from '../../dtos/prediction.interface';
import { InferenceResult } from '../inference-service.interface';
import {
    buildPredictionParams,
    convertPredictionsDTO,
    getAnnotationsFromDTO,
    getLimitedPredictedAnnotations,
} from '../utils';
import { VisualPromptService } from '../visual-prompt-service';
import { CreateApiService } from './utils';

export const createApiVisualPromptService: CreateApiService<VisualPromptService> = (
    { instance, router } = { instance: apiClient, router: API_URLS }
) => {
    const infer = async (
        datasetIdentifier: DatasetIdentifier,
        projectLabels: Label[],
        mediaItem: MediaItem,
        taskId: string,
        signal?: AbortSignal
    ): Promise<InferenceResult> => {
        if (isVideo(mediaItem)) {
            throw new Error('video is not supported');
        }

        try {
            const { data } = await instance.post<NewPredictionsDTO>(
                router.VISUAL_PROMPT_INFERENCE(datasetIdentifier, taskId),
                buildPredictionParams(mediaItem, datasetIdentifier),
                { signal }
            );

            if (!data) {
                return [];
            }

            const mediaIdentifierDTO = mediaIdentifierToDTO(mediaItem.identifier) as VideoFrameIdDTO | ImageIdDTO;
            const predictionsDTO = convertPredictionsDTO(data, mediaIdentifierDTO);

            return getLimitedPredictedAnnotations(getAnnotationsFromDTO(predictionsDTO.annotations, projectLabels));
        } catch {
            return [];
        }
    };

    return { infer };
};
