// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ValueType } from '@opentelemetry/api';
import { isEmpty } from 'lodash-es';

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
