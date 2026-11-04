// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { isEmpty } from 'lodash-es';

export enum WebhookHttpMethod {
    PUT = 'PUT',
    POST = 'POST',
    PATCH = 'PATCH',
}

const toStringAndTrim = (value: unknown) => String(value).trim();

export const getObjectFromFormData = (keys: FormDataEntryValue[], values: FormDataEntryValue[]) => {
    const entries = keys.map((key, index) => [key, values[index]]);
    const validEntries = entries.filter(
        ([key, value]) => !isEmpty(toStringAndTrim(key)) && !isEmpty(toStringAndTrim(value))
    );

    return Object.fromEntries(validEntries);
};

export const rateLimitFromFormData = (formData: FormData): number | null => {
    const samplesValue = formData.get('rate_limit_samples');
    const secondsValue = formData.get('rate_limit_seconds');

    if (samplesValue === null || secondsValue === null) {
        return null;
    }

    const samples = Number(samplesValue);
    const seconds = Number(secondsValue);

    if (!Number.isFinite(samples) || !Number.isFinite(seconds) || samples <= 0 || seconds <= 0) {
        return null;
    }

    return samples / seconds;
};
