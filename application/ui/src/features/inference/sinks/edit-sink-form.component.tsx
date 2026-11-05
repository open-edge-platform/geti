// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { assertNever } from '../../../shared/util';
import { EditLocalFolderSink } from './local-folder/edit-local-folder-sink.component';
import { EditMqttSink } from './mqtt/edit-mqtt-sink.component';
import type { EditSinkProps, SupportedSinkConfig } from './types';
import { EditWebhookSink } from './webhook/edit-webhook-sink.component';

interface EditSinkFormProps extends Omit<EditSinkProps<SupportedSinkConfig>, 'sink'> {
    config: SupportedSinkConfig;
}

export const EditSinkForm = ({ config, ...props }: EditSinkFormProps) => {
    switch (config.sink_type) {
        case 'folder':
            return <EditLocalFolderSink sink={config} {...props} />;
        case 'webhook':
            return <EditWebhookSink sink={config} {...props} />;
        case 'mqtt':
            return <EditMqttSink sink={config} {...props} />;
        default:
            return assertNever(config);
    }
};
