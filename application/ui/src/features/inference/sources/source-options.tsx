// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from 'react';

import { IpCamera as IpCameraIcon, VideoFile as VideoFileIcon, Webcam as WebcamIcon } from '@/assets/icons';
import { useTranslation } from '@/i18n';

import { DisclosureGroup } from '../shared/disclosure-group/disclosure-group.component';
import { AddIpCameraSource } from './ip-camera/add-ip-camera-source.component';
import type { AddSourceProps } from './types';
import { AddUsbCameraSource } from './usb-camera/add-usb-camera-source.component';
import { AddVideoFileSource } from './video-file/add-video-file-source.component';

interface SourceOptionsProps extends AddSourceProps {
    hasHeader: boolean;
    children: ReactNode;
}

export const SourceOptions = ({ onSaved, hasHeader, children, existingNames }: SourceOptionsProps) => {
    const { t } = useTranslation();

    return (
        <>
            {hasHeader && children}

            <DisclosureGroup
                defaultActiveInput={null}
                items={[
                    {
                        label: t('inference.sources.options.usbCamera'),
                        value: 'usb_camera',
                        icon: <WebcamIcon width={'24px'} />,
                        content: <AddUsbCameraSource existingNames={existingNames} onSaved={onSaved} />,
                    },
                    {
                        label: t('inference.sources.options.ipCamera'),
                        value: 'ip_camera',
                        icon: <IpCameraIcon width={'24px'} />,
                        content: <AddIpCameraSource existingNames={existingNames} onSaved={onSaved} />,
                    },
                    {
                        label: t('inference.sources.options.videoFile'),
                        value: 'video_file',
                        icon: <VideoFileIcon width={'24px'} />,
                        content: <AddVideoFileSource existingNames={existingNames} onSaved={onSaved} />,
                    },
                ]}
            />
        </>
    );
};
