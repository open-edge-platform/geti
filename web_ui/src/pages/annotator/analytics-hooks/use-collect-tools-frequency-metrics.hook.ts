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
import isEmpty from 'lodash/isEmpty';

import { useAnalytics } from '../../../analytics/analytics-provider.component';
import { getMetricName } from '../../../analytics/metrics';
import { useAnalyticsAnnotationTools } from '../providers/analytics-annotation-scene-provider/analytics-annotation-scene-provider.component';
import { getToolFrequencyUsage } from './utils';

interface UseCollectToolsFrequencyMetrics {
    collectToolsFrequencyMetric: () => void;
}

export const useCollectToolsFrequencyMetrics = (taskName: string): UseCollectToolsFrequencyMetrics => {
    const { toolPerAnnotation, resetToolPerAnnotation } = useAnalyticsAnnotationTools();
    const { meter } = useAnalytics();

    const collectToolsFrequencyMetric = () => {
        if (isEmpty(toolPerAnnotation)) {
            return;
        }

        const annotatorToolsCounter = meter?.createCounter(getMetricName('media.annotations.tools'), {
            description: 'Metrics for frequency of usage annotation tools',
            valueType: ValueType.INT,
        });

        const frequencies = getToolFrequencyUsage(toolPerAnnotation);

        Object.entries(frequencies).forEach(([toolName, count]) => {
            annotatorToolsCounter?.add(count, {
                toolName,
                label: taskName,
            });
        });

        resetToolPerAnnotation();
    };

    return { collectToolsFrequencyMetric };
};
