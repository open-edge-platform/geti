// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { get } from 'lodash-es';

import { ModelsGroups } from '../../core/models/models.interface';
import { ModelDetails, OptimizationTypes } from '../../core/models/optimized-models.interface';
import { OPTIMIZATION_TYPES_MAP } from '../../core/tests/services/utils';
import { MetricType } from '../../core/tests/tests.interface';
import { getPlural, isNonEmptyArray } from '../../shared/utils';
import { PreselectedModel, SelectableOptimizationType } from './project-details.interface';

type TestOptimizationTypes = Record<OptimizationTypes, SelectableOptimizationType>;

export const TESTS_OPTIMIZATION_TYPES: TestOptimizationTypes = {
    BASE: {
        text: OPTIMIZATION_TYPES_MAP.BASE,
        id: '',
    },
    MO: { text: OPTIMIZATION_TYPES_MAP.MO, id: '' },
    POT: { text: OPTIMIZATION_TYPES_MAP.POT, id: '' },
    ONNX: { text: OPTIMIZATION_TYPES_MAP.ONNX, id: '' },
    PYTORCH: { text: OPTIMIZATION_TYPES_MAP.PYTORCH, id: '' },
};

export const METRIC_ITEMS = [
    {
        id: 'image-score',
        name: MetricType.IMAGE_SCORE,
    },
    { id: 'object-score', name: MetricType.OBJECT_SCORE },
];

export const NO_MODELS_MESSAGE = 'No trained models. Go to the annotation tool and annotate images/frames.';
export const NO_MODELS_MESSAGE_TASK_CHAIN =
    'One or more tasks do not have trained models. Go to the annotation tool and annotate images/frames.';
export const TESTING_SET_WAS_TESTED_WITH_THIS_CONFIGURATION_MESSAGE =
    'This testing set has been tested with this configuration.';
export const DEFAULT_DATASET_MESSAGE = 'This is your training set, it is not recommended to use as a testing set.';

export const formatModelName = (modelName: string) => {
    // e.g. "ATSS OpenVINO FP16", we want everything but the first word (architecture)
    const [, ...rest] = modelName.split(' ');

    return rest.join(' '); // "OpenVINO FP16"
};

export interface AvailableOptimizationTypes {
    id: string;
    modelName: string;
    optimizationType: OptimizationTypes;
}

export const getAvailableOptimizationTypes = (
    optimizationTypes: AvailableOptimizationTypes[] | undefined
): SelectableOptimizationType[] => {
    if (!isNonEmptyArray(optimizationTypes)) {
        return [];
    }

    return (
        optimizationTypes
            // TODO: add support for onnx/pytorch models when downloading deployment code
            .filter(
                (optimizationType) =>
                    optimizationType.optimizationType !== 'ONNX' && optimizationType.optimizationType !== 'PYTORCH'
            )
            .map<SelectableOptimizationType>(({ id, modelName }) => ({
                id,
                text: formatModelName(modelName),
            }))
    );
};

export const getOptimizationTypes = (modelDetails?: ModelDetails): AvailableOptimizationTypes[] => {
    return (modelDetails?.optimizedModels ?? [])
        .filter(({ modelStatus }) => modelStatus === 'SUCCESS')
        .map(({ optimizationType, id, modelName }) => ({ id, optimizationType, modelName }));
};

export const getModels = (
    preselectedModel: PreselectedModel | undefined,
    modelsGroups: ModelsGroups[] | undefined,
    taskId: Key | null
) => {
    return preselectedModel
        ? [
              {
                  groupName: preselectedModel.groupName,
                  groupId: preselectedModel.groupId,
                  taskId: preselectedModel.taskId,
                  modelTemplateName: preselectedModel.templateName,
                  modelVersions: [
                      {
                          version: preselectedModel.version,
                          id: preselectedModel.id,
                      },
                  ],
              },
          ]
        : getTaskModels(modelsGroups, taskId);
};

export const getTaskModels = (modelsGroups?: ModelsGroups[], taskId?: Key | null): ModelsGroups[] => {
    return modelsGroups?.filter((modelsGroup) => taskId === modelsGroup.taskId) ?? [];
};

export const getMatchedMediaCounts = (
    totalMatchedImages: number,
    totalMatchedVideoFrames: number,
    totalMatchedVideos: number
): string => {
    const imagesText = `${totalMatchedImages} image${getPlural(totalMatchedImages)}`;
    const framesText = `${totalMatchedVideoFrames} frame${getPlural(totalMatchedVideoFrames)}`;
    const videosText = `${totalMatchedVideos} video${getPlural(totalMatchedVideos)}`;

    return `${imagesText}, ${framesText} from ${videosText}`;
};

export const getTotalMediaCounts = (totalImages: number, totalVideos: number): string => {
    const imagesText = `${totalImages} image${getPlural(totalImages)}`;

    if (totalVideos == 0) {
        return imagesText;
    }

    const videosText = `${totalVideos} video${getPlural(totalVideos)}`;

    return `${imagesText}, ${videosText}`;
};

export const isModelDeleted = (model: unknown) => {
    return get(model, 'purgeInfo.isPurged') === true;
};
