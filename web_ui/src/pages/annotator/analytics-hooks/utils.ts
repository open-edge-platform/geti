// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { hasEqualId } from '@shared/utils';
import countBy from 'lodash/countBy';
import isEqual from 'lodash/isEqual';

import { Annotation } from '../../../core/annotations/annotation.interface';
import { ToolPerAnnotation } from '../providers/analytics-annotation-scene-provider/use-enhanced-analytics-annotation-scene.hook';
import { areLabelsIdentical } from '../utils';

export const getUniqueModelIds = (predictions: readonly Annotation[]): string[] => {
    const uniqueModelIds = new Set<string>();

    predictions.forEach(({ labels }) => {
        labels.forEach(({ source }) => {
            source?.modelId && uniqueModelIds.add(source.modelId);
        });
    });

    return Array.from(uniqueModelIds);
};

export const getNumberOfNotEqualShapes = (
    predictions: readonly Annotation[],
    acceptedPredictions: readonly Annotation[]
): number => {
    return predictions.filter(
        (prediction) =>
            !acceptedPredictions.find(
                (acceptedPrediction) =>
                    hasEqualId(acceptedPrediction.id)(prediction) && isEqual(prediction.shape, acceptedPrediction.shape)
            )
    ).length;
};

export const getNumberOfNotEqualLabels = (
    predictions: readonly Annotation[],
    acceptedPredictions: readonly Annotation[]
) => {
    return predictions.filter(
        (prediction) =>
            !acceptedPredictions.find(
                (acceptedPrediction) =>
                    hasEqualId(acceptedPrediction.id)(prediction) &&
                    areLabelsIdentical(prediction.labels, acceptedPrediction.labels)
            )
    ).length;
};

export const getToolFrequencyUsage = (toolPerAnnotation: ToolPerAnnotation) => {
    const tools = Object.values(toolPerAnnotation);

    return countBy(tools);
};
