// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createI18nInstance } from '@/i18n';

import { getMockedModelArchitecture } from '../../../../../mocks/mock-model';
import { getAccuracyMetric } from './utils';

describe('getAccuracyMetric', () => {
    const { t } = createI18nInstance({ lng: 'en' });

    it('returns Top-1 Acc for classification tasks', () => {
        const modelArchitecture = getMockedModelArchitecture({
            task: 'classification',
            stats: {
                gigaflops: 1,
                trainable_parameters: 5,
                benchmark_metrics: {
                    imagenet_top1_accuracy: 76.2,
                    imagenet_top5_accuracy: 95.3,
                    coco_map_50_95: null,
                    coco_map_50: null,
                },
            },
        });

        const result = getAccuracyMetric(modelArchitecture, t);

        expect(result).toEqual({ label: 'Top-1 Acc on ImageNet', value: 76.2 });
    });

    it('returns mAP (50-95) for detection tasks', () => {
        const modelArchitecture = getMockedModelArchitecture({
            task: 'detection',
            stats: {
                gigaflops: 91,
                trainable_parameters: 31,
                benchmark_metrics: {
                    imagenet_top1_accuracy: null,
                    imagenet_top5_accuracy: null,
                    coco_map_50_95: 55.3,
                    coco_map_50: 72.1,
                },
            },
        });

        const result = getAccuracyMetric(modelArchitecture, t);

        expect(result).toEqual({ label: 'mAP on COCO', value: 55.3 });
    });

    it('falls back to coco_map_50 when coco_map_50_95 is null', () => {
        const modelArchitecture = getMockedModelArchitecture({
            task: 'detection',
            stats: {
                gigaflops: 91,
                trainable_parameters: 31,
                benchmark_metrics: {
                    imagenet_top1_accuracy: null,
                    imagenet_top5_accuracy: null,
                    coco_map_50_95: null,
                    coco_map_50: 72.1,
                },
            },
        });

        const result = getAccuracyMetric(modelArchitecture, t);

        expect(result).toEqual({ label: 'mAP50 on COCO', value: 72.1 });
    });

    it('returns undefined when no accuracy metrics are available', () => {
        const modelArchitecture = getMockedModelArchitecture({
            task: 'detection',
            stats: {
                gigaflops: 91,
                trainable_parameters: 31,
                benchmark_metrics: {
                    imagenet_top1_accuracy: null,
                    imagenet_top5_accuracy: null,
                    coco_map_50_95: null,
                    coco_map_50: null,
                },
            },
        });

        const result = getAccuracyMetric(modelArchitecture, t);

        expect(result).toBeUndefined();
    });
});
