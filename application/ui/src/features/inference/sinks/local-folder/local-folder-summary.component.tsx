// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LocalFolderSinkConfig } from '@/api/types';
import { useTranslation } from '@/i18n';

import { OutputFormatsList } from '../sink-list/sinks-details/output-formats-list.component';
import { formatRateLimit } from '../utils';

interface LocalFolderSummaryProps {
    sink: LocalFolderSinkConfig;
}

export const LocalFolderSummary = ({ sink }: LocalFolderSummaryProps) => {
    const { t } = useTranslation();

    return (
        <>
            <li>{t('inference.settings.folderPath', { path: sink.folder_path })}</li>
            <li>{t('inference.sinks.settings.rateLimit', { value: formatRateLimit(sink.rate_limit, t) })}</li>
            <OutputFormatsList outputFormats={sink.output_formats} />
        </>
    );
};
