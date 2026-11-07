// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from 'react';

import { Folder as FolderIcon, Mqtt as MqttIcon, Webhook as WebhookIcon } from '@/assets/icons';
import { useTranslation } from '@/i18n';

import { DisclosureGroup } from '../shared/disclosure-group/disclosure-group.component';
import { AddLocalFolderSink } from './local-folder/add-local-folder-sink.component';
import { AddMqttSink } from './mqtt/add-mqtt-sink.component';
import type { AddSinkProps } from './types';
import { AddWebhookSink } from './webhook/add-webhook-sink.component';

interface SinkOptionsProps extends AddSinkProps {
    hasHeader: boolean;
    children: ReactNode;
}

export const SinkOptions = ({ onSaved, hasHeader, children }: SinkOptionsProps) => {
    const { t } = useTranslation();

    return (
        <>
            {hasHeader && children}

            <DisclosureGroup
                defaultActiveInput={null}
                items={[
                    {
                        label: t('inference.sinks.options.folder'),
                        value: 'folder',
                        icon: <FolderIcon width={'24px'} />,
                        content: <AddLocalFolderSink onSaved={onSaved} />,
                    },
                    {
                        label: t('inference.sinks.options.webhook'),
                        value: 'webhook',
                        icon: <WebhookIcon width={'24px'} />,
                        content: <AddWebhookSink onSaved={onSaved} />,
                    },
                    {
                        label: t('inference.sinks.options.mqtt'),
                        value: 'mqtt',
                        icon: <MqttIcon width={'24px'} />,
                        content: <AddMqttSink onSaved={onSaved} />,
                    },
                ]}
            />
        </>
    );
};
