// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { TranslateFn } from '@/i18n';

export enum OutputFormat {
    IMAGE_ORIGINAL = 'image_original',
    IMAGE_WITH_PREDICTIONS = 'image_with_predictions',
    PREDICTIONS = 'predictions',
}

export const positiveNumberOrUndefined = (value: number | null | undefined): number | undefined => {
    return typeof value === 'number' && value > 0 ? value : undefined;
};

export const formatRateLimit = (rateLimit: number | null | undefined, t: TranslateFn): string => {
    const normalizedRateLimit = positiveNumberOrUndefined(rateLimit);

    if (normalizedRateLimit === undefined) {
        return t('inference.sinks.rateLimit.notSet');
    }

    if (normalizedRateLimit < 1) {
        const seconds = 1 / normalizedRateLimit;
        const normalizedSeconds = Math.round(seconds);

        return t('inference.sinks.rateLimit.oneSamplePerSeconds', { count: normalizedSeconds });
    }

    const normalizedSamples = Math.round(normalizedRateLimit);

    return t('inference.sinks.rateLimit.samplesPerSecond', { count: normalizedSamples });
};
