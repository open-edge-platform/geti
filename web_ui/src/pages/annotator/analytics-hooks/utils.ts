// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import countBy from 'lodash/countBy';
import isEqual from 'lodash/isEqual';

import { Annotation } from '../../../core/annotations/annotation.interface';
import { hasEqualId } from '../../../shared/utils';
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
