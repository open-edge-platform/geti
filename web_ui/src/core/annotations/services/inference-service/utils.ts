// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AxiosInstance } from 'axios';
import { isNil } from 'lodash-es';
import { v4 as uuidv4 } from 'uuid';

import { Label } from '../../../labels/label.interface';
import { MediaItem } from '../../../media/media.interface';
import { API_URLS } from '../../../services/urls';
import { Annotation, TaskChainInput } from '../../annotation.interface';
import { AnnotationLabelDTO, ImageIdDTO, VideoFrameIdDTO } from '../../dtos/annotation.interface';
import { NewPredictionsDTO } from '../../dtos/prediction.interface';
import { Rect } from '../../shapes.interface';
import { convertPredictionsDTO, getAnnotationsFromDTO, getLimitedPredictedAnnotations } from '../utils';

export interface CreateApiService<Type> {
    (arg?: { instance: AxiosInstance; router: typeof API_URLS }): Type;
}

export interface BatchPredictionDTO extends NewPredictionsDTO {
    media_identifier: VideoFrameIdDTO;
}

export interface BatchPredictionsDTO {
    batch_predictions: (BatchPredictionDTO | null)[];
}

export const getInputShapeRect = (selectedInput: TaskChainInput) => {
    const { shapeType: _removedShapeType, ...roiConfig } = selectedInput.shape as Rect;

    return roiConfig;
};

export const hasEmptyLabel = (projectLabels: Label[]) => (predictionLabel: AnnotationLabelDTO) => {
    return projectLabels.some((label) => label.isEmpty && label.id === predictionLabel.id);
};

export const getExplanationRoi = (mediaItem: MediaItem, selectedInput?: TaskChainInput) => {
    return isNil(selectedInput)
        ? {
              id: uuidv4(),
              x: 0,
              y: 0,
              width: mediaItem.metadata.width,
              height: mediaItem.metadata.height,
          }
        : {
              id: selectedInput.id,
              ...getInputShapeRect(selectedInput),
          };
};

export const convertDtosToAnnotations = (
    predictions: NewPredictionsDTO,
    mediaIdentifier: VideoFrameIdDTO | ImageIdDTO,
    projectLabels: Label[]
) => {
    const predictionDTO = convertPredictionsDTO(predictions, mediaIdentifier);

    return getLimitedPredictedAnnotations(getAnnotationsFromDTO(predictionDTO.annotations, projectLabels));
};

export const convertBatchToRecord = (batch_predictions: (BatchPredictionDTO | null)[], projectLabels: Label[]) =>
    batch_predictions.reduce<Record<number, Annotation[]>>((accumulator, predictions) => {
        if (isNil(predictions)) {
            return accumulator;
        }

        const frame_index = parseInt(predictions.media_identifier.frame_index.toString());
        const mediaIdentifier = { ...predictions.media_identifier, frame_index };
        accumulator[frame_index] = convertDtosToAnnotations(predictions, mediaIdentifier, projectLabels);

        return accumulator;
    }, {});
