// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import type { SourceConfig } from '@/api/types';
import { useTranslation } from 'react-i18next';

import classes from './settings-list.module.scss';

interface SettingsListProps {
    source: SourceConfig;
}

const CameraDeviceDisplay = ({ deviceId }: { deviceId: number }) => {
    const { t } = useTranslation();
    const { data: cameraDevices = [], isLoading } = $api.useQuery('get', '/api/system/devices/camera');
    const device = cameraDevices.find(({ index }) => index === deviceId);

    if (isLoading) {
        return <span>{t('inference.loadingText')}</span>;
    }

    return (
        <ul className={classes.list}>
            <li>
                {t('inference.deviceLabelDetail')}: {device ? device.name : t('inference.unknownDeviceAria')}
            </li>
        </ul>
    );
};

export const SettingsList = ({ source }: SettingsListProps) => {
    const { t } = useTranslation();

    if (source.source_type === 'images_folder') {
        return (
            <ul className={classes.list}>
                <li>
                    {t('inference.folderPathLabel')}: {source.images_folder_path}
                </li>
                <li>
                    {t('inference.ignoreExistingImagesLabel')}:{' '}
                    {source.ignore_existing_images ? t('common.yes') : t('common.no')}
                </li>
            </ul>
        );
    }

    if (source.source_type === 'ip_camera') {
        return (
            <ul className={classes.list}>
                <li>
                    {t('inference.streamUrlLabel')}: {source.stream_url}
                </li>
                <li>
                    {t('inference.authRequiredDetail')}: {source.auth_required ? t('common.yes') : t('common.no')}
                </li>
            </ul>
        );
    }

    if (source.source_type === 'video_file') {
        return (
            <ul className={classes.list}>
                <li>
                    {t('inference.videoPathLabelDetail')}: {source.video_path}
                </li>
            </ul>
        );
    }

    if (source.source_type === 'usb_camera') {
        return <CameraDeviceDisplay deviceId={source.device_id} />;
    }

    return <></>;
};
