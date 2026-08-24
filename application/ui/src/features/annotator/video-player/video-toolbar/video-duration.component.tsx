// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { MediaVideoFrame } from '@/api/types';
import { useTranslation } from 'react-i18next';

import { formatDurationText } from './time-utils';

type VideoDurationProps = {
    videoFrame: MediaVideoFrame;
};

export const VideoDuration = ({ videoFrame }: VideoDurationProps) => {
    const { t } = useTranslation();

    const currentTime = videoFrame.frame_number / videoFrame.fps;
    const endTime = videoFrame.duration;

    const currentFormattedTime = formatDurationText(currentTime);
    const endFormattedTime = formatDurationText(endTime);

    return (
        <span aria-label={t('annotator.videoDurationAria')}>
            {currentFormattedTime} / {endFormattedTime}
        </span>
    );
};
