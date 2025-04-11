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

import { Label } from '../../../labels/label.interface';
import { MediaItem } from '../../../media/media.interface';
import { mediaIdentifierToDTO } from '../../../media/services/utils';
import { isVideo } from '../../../media/video.interface';
import { DatasetIdentifier } from '../../../projects/dataset.interface';
import { instance as defaultAxiosInstance } from '../../../services/axios-instance';
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
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
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
