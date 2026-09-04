// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { ModelArchitectureWithPerformanceCategory } from '@/api/types';
import { orderBy } from 'lodash-es';

import { TIMM_MODEL_ARCHITECTURE_ID } from '../timm-model-configuration/utils';

export const SortingOptions = {
    NAME_ASC: 'name-asc',
    NAME_DESC: 'name-desc',
    SPEED_ASC: 'speed-asc',
    SPEED_DESC: 'speed-desc',
    ACCURACY_ASC: 'accuracy-asc',
    ACCURACY_DESC: 'accuracy-desc',
} as const;

export type SortingOptions = (typeof SortingOptions)[keyof typeof SortingOptions];

type SortingHandler = (
    modelArchitectures: ModelArchitectureWithPerformanceCategory[]
) => ModelArchitectureWithPerformanceCategory[];

const getAccuracyMetricBasedOnTask = ({ stats }: ModelArchitectureWithPerformanceCategory) => {
    const benchmarkMetrics = stats?.benchmark_metrics;

    return (
        benchmarkMetrics?.imagenet_top1_accuracy ?? benchmarkMetrics?.coco_map_50_95 ?? benchmarkMetrics?.coco_map_50
    );
};

// Pins the synthetic TIMM card to the last position regardless of the chosen sort.
const pinTimmCardLast = (handler: SortingHandler): SortingHandler => (modelArchitectures) => {
    const timmCard = modelArchitectures.filter(({ id }) => id === TIMM_MODEL_ARCHITECTURE_ID);
    const rest = modelArchitectures.filter(({ id }) => id !== TIMM_MODEL_ARCHITECTURE_ID);

    return [...handler(rest), ...timmCard];
};

export const SORTING_HANDLERS: Record<SortingOptions, SortingHandler> = {
    [SortingOptions.ACCURACY_ASC]: pinTimmCardLast((modelArchitectures) =>
        orderBy(modelArchitectures, getAccuracyMetricBasedOnTask, 'asc')
    ),
    [SortingOptions.ACCURACY_DESC]: pinTimmCardLast((modelArchitectures) =>
        orderBy(modelArchitectures, getAccuracyMetricBasedOnTask, 'desc')
    ),
    [SortingOptions.NAME_ASC]: pinTimmCardLast((modelArchitectures) =>
        orderBy(modelArchitectures, (modelArchitecture) => modelArchitecture.name, 'asc')
    ),
    [SortingOptions.NAME_DESC]: pinTimmCardLast((modelArchitectures) =>
        orderBy(modelArchitectures, (modelArchitecture) => modelArchitecture.name, 'desc')
    ),
    [SortingOptions.SPEED_ASC]: pinTimmCardLast((modelArchitectures) =>
        orderBy(modelArchitectures, (modelArchitecture) => modelArchitecture.stats?.gigaflops, 'asc')
    ),
    [SortingOptions.SPEED_DESC]: pinTimmCardLast((modelArchitectures) =>
        orderBy(modelArchitectures, (modelArchitecture) => modelArchitecture.stats?.gigaflops, 'desc')
    ),
};

export const SORT_OPTIONS = [
    [
        {
            key: SortingOptions.NAME_ASC,
            name: 'Name (A to Z)',
        },
        {
            key: SortingOptions.NAME_DESC,
            name: 'Name (Z to A)',
        },
    ],
    [
        {
            key: SortingOptions.SPEED_ASC,
            name: 'Speed (fastest first)',
        },
        {
            key: SortingOptions.SPEED_DESC,
            name: 'Speed (slowest first)',
        },
    ],
    [
        {
            key: SortingOptions.ACCURACY_ASC,
            name: 'Accuracy (lowest first)',
        },
        {
            key: SortingOptions.ACCURACY_DESC,
            name: 'Accuracy (highest first)',
        },
    ],
];
