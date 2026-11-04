// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { WebhookSinkConfig } from '@/api/types';

import { EditSink } from '../deprecated/edit-sink/edit-sink.component';
import { webhookBodyFormatter } from '../deprecated/webhook/utils';
import { Webhook } from '../deprecated/webhook/webhook.component';
import type { EditSinkProps } from '../types';

export const EditWebhookSink = ({ sink, isConnected, onSaved, onBackToList }: EditSinkProps<WebhookSinkConfig>) => (
    <EditSink
        config={sink}
        isConnected={isConnected}
        onSaved={onSaved}
        onBackToList={onBackToList}
        componentFields={(state) => <Webhook defaultState={state} />}
        bodyFormatter={webhookBodyFormatter}
    />
);
