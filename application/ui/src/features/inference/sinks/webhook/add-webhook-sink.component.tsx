// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AddSink } from '../deprecated/add-sink/add-sink.component';
import { getWebhookInitialConfig, webhookBodyFormatter } from '../deprecated/webhook/utils';
import { Webhook } from '../deprecated/webhook/webhook.component';
import type { AddSinkProps } from '../types';

export const AddWebhookSink = ({ onSaved }: AddSinkProps) => (
    <AddSink
        onSaved={onSaved}
        config={getWebhookInitialConfig()}
        componentFields={(state) => <Webhook defaultState={state} />}
        bodyFormatter={webhookBodyFormatter}
    />
);
