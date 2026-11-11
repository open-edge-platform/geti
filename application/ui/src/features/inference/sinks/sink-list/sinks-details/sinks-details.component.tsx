// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SinkConfig } from '@/api/types';

import { assertNever } from '../../../../../shared/util';
import { LocalFolderSummary } from '../../local-folder/local-folder-summary.component';
import { MqttSummary } from '../../mqtt/mqtt-summary.component';
import { WebhookSummary } from '../../webhook/webhook-summary.component';

import classes from './sinks-details.module.scss';

interface SinksDetailsProps {
    sink: SinkConfig;
}

const SinkSummary = ({ sink }: SinksDetailsProps) => {
    switch (sink.sink_type) {
        case 'folder':
            return <LocalFolderSummary sink={sink} />;
        case 'mqtt':
            return <MqttSummary sink={sink} />;
        case 'webhook':
            return <WebhookSummary sink={sink} />;
        default:
            return assertNever(sink);
    }
};

export const SinksDetails = ({ sink }: SinksDetailsProps) => (
    <ul className={classes.list}>
        <SinkSummary sink={sink} />
    </ul>
);
