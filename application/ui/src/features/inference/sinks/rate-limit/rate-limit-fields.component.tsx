// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Flex, NumberField, Text } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { positiveNumberOrUndefined } from '../utils';

type RateLimitFieldsProps = {
    rateLimit: number | null | undefined;
};

export const RateLimitFields = ({ rateLimit }: RateLimitFieldsProps) => {
    const { t } = useTranslation();

    const samples = positiveNumberOrUndefined(rateLimit);
    const seconds = samples !== undefined ? 1 : undefined;

    return (
        <Flex gap='size-100' alignItems={'end'} wrap>
            <NumberField
                label={t('inference.samplesLabel')}
                name='rate_limit_samples'
                minValue={0.1}
                step={0.1}
                defaultValue={samples}
            />
            <Text>every</Text>
            <NumberField
                label={t('inference.secondsLabel')}
                name='rate_limit_seconds'
                minValue={0.1}
                step={0.1}
                defaultValue={seconds}
            />
        </Flex>
    );
};
