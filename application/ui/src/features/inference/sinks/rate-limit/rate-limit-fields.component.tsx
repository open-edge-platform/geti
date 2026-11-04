// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { useTranslation } from '@/i18n';
import { Flex, NumberField, Text } from '@geti-ui/ui';

import { positiveNumberOrUndefined, toRateLimit } from '../utils';

interface RateLimitFieldsProps {
    value: number | null;
    onChange: (value: number | null) => void;
}

const toNumberOrNull = (value: number): number | null => (Number.isNaN(value) ? null : value);

export const RateLimitFields = ({ value, onChange }: RateLimitFieldsProps) => {
    const { t } = useTranslation();
    const [samples, setSamples] = useState<number | null>(() => positiveNumberOrUndefined(value) ?? null);
    const [seconds, setSeconds] = useState<number | null>(() => (positiveNumberOrUndefined(value) ? 1 : null));

    const handleSamplesChange = (next: number) => {
        const nextSamples = toNumberOrNull(next);

        setSamples(nextSamples);
        onChange(toRateLimit(nextSamples, seconds));
    };

    const handleSecondsChange = (next: number) => {
        const nextSeconds = toNumberOrNull(next);

        setSeconds(nextSeconds);
        onChange(toRateLimit(samples, nextSeconds));
    };

    return (
        <Flex gap='size-100' alignItems={'end'} wrap>
            <NumberField
                label={t('inference.sinks.fields.samples')}
                minValue={0.1}
                step={0.1}
                value={samples ?? Number.NaN}
                onChange={handleSamplesChange}
            />
            <Text>{t('common.labels.every')}</Text>
            <NumberField
                label={t('common.labels.seconds')}
                minValue={0.1}
                step={0.1}
                value={seconds ?? Number.NaN}
                onChange={handleSecondsChange}
            />
        </Flex>
    );
};
