// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SinkOutputFormats } from '@/api/types';
import { useTranslation } from '@/i18n';

import { OutputFormat } from '../../utils';

const OUTPUT_FORMAT_TYPE_LABEL_KEYS = {
    [OutputFormat.IMAGE_ORIGINAL]: 'inference.sinks.settings.outputFormatTypes.imageOriginal',
    [OutputFormat.IMAGE_WITH_PREDICTIONS]: 'inference.sinks.settings.outputFormatTypes.imageWithPredictions',
    [OutputFormat.PREDICTIONS]: 'inference.sinks.settings.outputFormatTypes.predictions',
} as const;

interface OutputFormatsListProps {
    outputFormats: SinkOutputFormats;
}

export const OutputFormatsList = ({ outputFormats }: OutputFormatsListProps) => {
    const { t } = useTranslation();

    return (
        <li>
            {t('inference.sinks.settings.outputFormats')}
            <ul>
                {outputFormats.map((item) => (
                    <li key={item}>{t(OUTPUT_FORMAT_TYPE_LABEL_KEYS[item])}</li>
                ))}
            </ul>
        </li>
    );
};
