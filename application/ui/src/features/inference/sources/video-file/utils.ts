// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { VideoFileSourceConfig } from '@/api/types';
import type { TranslateFn } from '@/i18n';

import { getUniqueName } from '../utils';

export type VideoFileFormState = Omit<VideoFileSourceConfig, 'id'>;

export const getVideoFileInitialConfig = (t: TranslateFn, existingNames: string[] = []): VideoFileFormState => ({
    name: getUniqueName(t('inference.sources.defaultNames.videoFile'), existingNames),
    source_type: 'video_file',
    video_path: '',
    loop: false,
});
