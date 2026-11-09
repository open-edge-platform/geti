// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { BenchmarkMetrics, ModelArchitecture } from '@/api/types';
import type { TranslateFn } from '@/i18n';
import { isNil } from 'lodash-es';

type AccuracyMetric = { label: string; value: number };

type BenchmarkMetricKey = keyof BenchmarkMetrics;

const getAccuracyMetricLabels = (t: TranslateFn): Partial<Record<BenchmarkMetricKey, string>> => ({
    imagenet_top1_accuracy: t('models.training.architectures.metrics.top1AccOnImageNet'),
    coco_map_50_95: t('models.training.architectures.metrics.mapOnCoco'),
    coco_map_50: t('models.training.architectures.metrics.map50OnCoco'),
});

export const getAccuracyMetric = (modelArchitecture: ModelArchitecture, t: TranslateFn): AccuracyMetric | undefined => {
    const benchmarkMetrics = modelArchitecture.stats?.benchmark_metrics;

    for (const [key, label] of Object.entries(getAccuracyMetricLabels(t))) {
        const value = benchmarkMetrics?.[key as BenchmarkMetricKey];

        if (!isNil(value)) {
            return { label, value };
        }
    }

    return undefined;
};
