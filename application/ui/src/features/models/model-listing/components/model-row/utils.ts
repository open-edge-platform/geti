// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Evaluation, Metric, Model, TaskType } from '@/api/types';
import type { TranslateFn } from '@/i18n';

import { isClassificationTask } from '../../../../../shared/task-type-guards';

export const getModelEvaluations = (model: Model): Evaluation[] => {
    return model.variants.flatMap((variant) => variant.evaluations);
};

const getDefaultPerformanceMetricName = (taskType: TaskType | null): string => {
    return isClassificationTask(taskType) ? 'Accuracy' : 'mAP';
};

// Acronyms such as mAP and mAR are shown as the API returns them.
const METRIC_LABEL_KEYS = {
    Accuracy: 'models.performance.metrics.accuracy',
    Precision: 'models.performance.metrics.precision',
    Recall: 'models.performance.metrics.recall',
    'F-measure': 'models.performance.metrics.fMeasure',
} as const satisfies Partial<Record<Metric['name'], string>>;

const isTranslatableMetric = (name: string): name is keyof typeof METRIC_LABEL_KEYS =>
    Object.hasOwn(METRIC_LABEL_KEYS, name);

export const getMetricLabel = (name: string, t: TranslateFn): string =>
    isTranslatableMetric(name) ? t(METRIC_LABEL_KEYS[name]) : name;

const getTestingEvaluation = (evaluations: Evaluation[]): Evaluation | undefined => {
    return evaluations.find(({ subset }) => subset === 'testing');
};

export const getTestingMetrics = (evaluations: Evaluation[]): Metric[] => {
    return getTestingEvaluation(evaluations)?.metrics ?? [];
};

export const getTestingMetric = (model: Model): { name: string; value: number } | undefined => {
    const primaryMetric = getTestingMetrics(getModelEvaluations(model)).find(({ primary }) => primary);

    if (primaryMetric !== undefined) {
        return { name: primaryMetric.name, value: Math.round(primaryMetric.value * 100) };
    }

    return undefined;
};

export const getFirstAvailableTestingMetric = (
    models: Model[] | undefined
): { name: string; value: number } | undefined => {
    // Should never happen, but just in case
    if (models === undefined) {
        return undefined;
    }

    for (const model of models) {
        const testingMetric = getTestingMetric(model);

        if (testingMetric !== undefined) {
            return testingMetric;
        }
    }

    return undefined;
};

export const getPerformanceColumnAriaLabel = (models: Model[] | undefined, taskType: TaskType | null): string => {
    return getFirstAvailableTestingMetric(models)?.name ?? getDefaultPerformanceMetricName(taskType);
};

export const getPerformanceColumnLabel = (
    models: Model[] | undefined,
    taskType: TaskType | null,
    t: TranslateFn
): string => {
    return getMetricLabel(getPerformanceColumnAriaLabel(models, taskType), t);
};
