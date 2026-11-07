// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SourceConfigPayload } from '@/api/types';
import { IpCamera as IpCameraIcon, VideoFile as VideoFileIcon, Webcam as WebcamIcon } from '@/assets/icons';

import { assertNever } from '../../../../../shared/util';

interface SourceIconProps {
    type: SourceConfigPayload['source_type'];
}

export const SourceIcon = ({ type }: SourceIconProps) => {
    switch (type) {
        case 'usb_camera':
            return <WebcamIcon />;
        case 'ip_camera':
            return <IpCameraIcon />;
        case 'video_file':
            return <VideoFileIcon />;
        default:
            return assertNever(type);
    }
};
