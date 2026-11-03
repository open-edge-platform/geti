// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SourceConfigPayload } from '@/api/types';

import { assertNever } from '../../../../../shared/util';
import { IpCameraSummary } from '../../ip-camera/ip-camera-summary.component';
import { UsbCameraSummary } from '../../usb-camera/usb-camera-summary.component';
import { VideoFileSummary } from '../../video-file/video-file-summary.component';

import classes from './settings-list.module.scss';

interface SettingsListProps {
    source: SourceConfigPayload;
}

const SourceSummary = ({ source }: SettingsListProps) => {
    switch (source.source_type) {
        case 'usb_camera':
            return <UsbCameraSummary source={source} />;
        case 'ip_camera':
            return <IpCameraSummary source={source} />;
        case 'video_file':
            return <VideoFileSummary source={source} />;
        default:
            return assertNever(source);
    }
};

export const SettingsList = ({ source }: SettingsListProps) => (
    <ul className={classes.list}>
        <SourceSummary source={source} />
    </ul>
);
