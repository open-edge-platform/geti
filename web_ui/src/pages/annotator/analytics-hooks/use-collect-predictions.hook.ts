// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ValueType } from '@opentelemetry/api';

import { useAnalytics } from '../../../analytics/analytics-provider.component';
import { getMetricName } from '../../../analytics/metrics';
import { Annotation } from '../../../core/annotations/annotation.interface';
import { areAnnotationsIdentical } from '../utils';
import { getNumberOfNotEqualLabels, getNumberOfNotEqualShapes, getUniqueModelIds } from './utils';

interface UseCollectPredictions {
    collectPredictionsMetric: (predictions: readonly Annotation[], acceptedPredictions: Annotation[]) => void;
}

const PREDICTION_METRIC_PREFIX = 'suggestions.';
const PREDICTION_METRIC_EDITED_PREFIX = `${PREDICTION_METRIC_PREFIX}edited.`;
const PREDICTION_METRIC_UNEDITED_PREFIX = `${PREDICTION_METRIC_PREFIX}unedited.`;

export const useCollectPredictions = (taskName: string): UseCollectPredictions => {
    const { meter } = useAnalytics();
    const requiredMetricAttributes = {
        label: taskName,
    };

    const collectPredictionsMetric = (predictions: readonly Annotation[], acceptedPredictions: Annotation[]): void => {
        if (areAnnotationsIdentical(predictions, acceptedPredictions)) {
            collectUneditedPredictions(predictions);
        } else {
            collectEditedPredictions(predictions, acceptedPredictions);
        }
    };

    const collectUneditedPredictions = (predictions: readonly Annotation[]): void => {
        const uneditedPredictionsMediaCounter = meter?.createCounter(
            getMetricName(`${PREDICTION_METRIC_UNEDITED_PREFIX}media`),
            {
                description: 'Metrics for accepted media items in the suggestions',
                valueType: ValueType.INT,
            }
        );

        const uneditedPredictionsShapesCounter = meter?.createCounter(
            getMetricName(`${PREDICTION_METRIC_UNEDITED_PREFIX}shapes`),
            {
                description: 'Metrics for accepted shapes in the suggestions',
                valueType: ValueType.INT,
            }
        );

        const metricAttributes = {
            ...requiredMetricAttributes,
            modelId: getUniqueModelIds(predictions),
        };

        uneditedPredictionsShapesCounter?.add(predictions.length, metricAttributes);

        uneditedPredictionsMediaCounter?.add(1, metricAttributes);
    };

    const collectEditedPredictions = (predictions: readonly Annotation[], acceptedPredictions: Annotation[]): void => {
        const editedPredictionsShapesCounter = meter?.createCounter(
            getMetricName(`${PREDICTION_METRIC_EDITED_PREFIX}shapes`),
            {
                description: 'Metrics for edited shapes in the suggestions',
                valueType: ValueType.INT,
            }
        );

        const editedPredictionsLabelsCounter = meter?.createCounter(
            getMetricName(`${PREDICTION_METRIC_EDITED_PREFIX}labels`),
            {
                description: 'Metrics for edited labels in the suggestions',
                valueType: ValueType.INT,
            }
        );

        const editedPredictionsMediaCounter = meter?.createCounter(
            getMetricName(`${PREDICTION_METRIC_EDITED_PREFIX}media`),
            {
                description: 'Metrics for edited media items in the suggestions',
                valueType: ValueType.INT,
            }
        );

        const numberOfNotEqualShapes = getNumberOfNotEqualShapes(predictions, acceptedPredictions);

        const numberOfNotEqualLabels = getNumberOfNotEqualLabels(predictions, acceptedPredictions);

        const metricAttributes = {
            ...requiredMetricAttributes,
            totalNumberOfPredictions: predictions.length,
            modelId: getUniqueModelIds(acceptedPredictions),
        };

        numberOfNotEqualShapes > 0 && editedPredictionsShapesCounter?.add(numberOfNotEqualShapes, metricAttributes);

        numberOfNotEqualLabels > 0 && editedPredictionsLabelsCounter?.add(numberOfNotEqualLabels, metricAttributes);

        editedPredictionsMediaCounter?.add(1, metricAttributes);
    };

    return {
        collectPredictionsMetric,
    };
};
