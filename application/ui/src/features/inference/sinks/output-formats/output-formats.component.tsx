// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SinkOutputFormats } from '@/api/types';
import { useTranslation } from '@/i18n';
import { Checkbox, CheckboxGroup } from '@geti-ui/ui';

import { OutputFormat } from '../utils';

import classes from './output-formats.module.scss';

interface OutputFormatsProps {
    value: SinkOutputFormats;
    onChange: (value: SinkOutputFormats) => void;
}

export const OutputFormats = ({ value, onChange }: OutputFormatsProps) => {
    const { t } = useTranslation();

    return (
        <CheckboxGroup
            isRequired
            label={t('inference.sinks.fields.outputFormatsLabel')}
            value={value}
            onChange={(next) => onChange(next as SinkOutputFormats)}
            UNSAFE_className={classes.itemList}
        >
            <Checkbox value={OutputFormat.PREDICTIONS}>{t('inference.sinks.fields.outputFormatPredictions')}</Checkbox>
            <Checkbox value={OutputFormat.IMAGE_ORIGINAL}>
                {t('inference.sinks.fields.outputFormatImageOriginal')}
            </Checkbox>
            <Checkbox value={OutputFormat.IMAGE_WITH_PREDICTIONS}>
                {t('inference.sinks.fields.outputFormatImageWithPredictions')}
            </Checkbox>
        </CheckboxGroup>
    );
};
