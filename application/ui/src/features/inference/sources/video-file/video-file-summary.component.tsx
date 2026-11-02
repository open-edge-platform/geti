// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { VideoFileSourceConfig } from '@/api/types';
import { useTranslation } from '@/i18n';

interface VideoFileSummaryProps {
    source: VideoFileSourceConfig;
}

export const VideoFileSummary = ({ source }: VideoFileSummaryProps) => {
    const { t } = useTranslation();

    return <li>{t('inference.sources.settings.videoPath', { path: source.video_path })}</li>;
};
