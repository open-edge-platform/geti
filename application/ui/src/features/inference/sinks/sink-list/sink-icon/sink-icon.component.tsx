// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Folder as FolderIcon, Mqtt as MqttIcon, Webhook as WebhookIcon } from '@/assets/icons';

import { assertNever } from '../../../../../shared/util';
import type { SupportedSinkConfig } from '../../types';

interface SinkIconProps {
    type: SupportedSinkConfig['sink_type'];
}

export const SinkIcon = ({ type }: SinkIconProps) => {
    switch (type) {
        case 'folder':
            return <FolderIcon />;
        case 'mqtt':
            return <MqttIcon />;
        case 'webhook':
            return <WebhookIcon />;
        default:
            return assertNever(type);
    }
};
