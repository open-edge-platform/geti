// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { LocalFolderSinkConfig } from '@/api/types';
import type { TranslateFn } from '@/i18n';

export const getLocalFolderInitialConfig = (t: TranslateFn): LocalFolderSinkConfig => ({
    id: '',
    name: t('inference.sinks.defaultNames.localFolder'),
    sink_type: 'folder',
    rate_limit: null,
    folder_path: '',
    output_formats: [],
});

export const isLocalFolderConfigComplete = ({ folder_path, output_formats }: LocalFolderSinkConfig): boolean =>
    folder_path.trim().length > 0 && output_formats.length > 0;
