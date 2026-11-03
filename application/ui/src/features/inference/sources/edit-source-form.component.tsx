// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SourceConfigPayload } from '@/api/types';

import { assertNever } from '../../../shared/util';
import { EditIpCameraSource } from './ip-camera/edit-ip-camera-source.component';
import type { EditSourceProps } from './types';
import { EditUsbCameraSource } from './usb-camera/edit-usb-camera-source.component';
import { EditVideoFileSource } from './video-file/edit-video-file-source.component';

interface EditSourceFormProps extends Omit<EditSourceProps<SourceConfigPayload>, 'source'> {
    config: SourceConfigPayload;
}

export const EditSourceForm = ({ config, ...props }: EditSourceFormProps) => {
    switch (config.source_type) {
        case 'usb_camera':
            return <EditUsbCameraSource source={config} {...props} />;
        case 'ip_camera':
            return <EditIpCameraSource source={config} {...props} />;
        case 'video_file':
            return <EditVideoFileSource source={config} {...props} />;
        default:
            return assertNever(config);
    }
};
