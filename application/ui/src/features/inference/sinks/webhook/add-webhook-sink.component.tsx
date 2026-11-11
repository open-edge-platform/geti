// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useState } from 'react';

import { useTranslation } from '@/i18n';
import { Form } from '@geti-ui/ui';

import { useConnectSinkToPipeline } from '../../../../hooks/api/pipeline.hook';
import { AddSinkButton } from '../add-sink/add-sink-button.component';
import { useCreateSink } from '../api/use-create-sink';
import type { AddSinkProps } from '../types';
import { getWebhookInitialConfig, isWebhookConfigValid, toWebhookBody } from './utils';
import { WebhookFields } from './webhook-fields.component';

export const AddWebhookSink = ({ onSaved }: AddSinkProps) => {
    const { t } = useTranslation();
    const [config, setConfig] = useState(() => getWebhookInitialConfig(t));
    const createSink = useCreateSink();
    const connectSink = useConnectSinkToPipeline();

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();

        try {
            const { id } = await createSink.mutateAsync({ body: { sink_type: 'webhook', ...toWebhookBody(config) } });
            await connectSink.mutateAsync(id);
            onSaved();
        } catch {
            // toasts are handled by the hooks / MutationCache
        }
    };

    return (
        <Form validationBehavior='native' onSubmit={handleSubmit}>
            <WebhookFields value={config} onChange={setConfig} />
            <AddSinkButton
                isPending={createSink.isPending || connectSink.isPending}
                isDisabled={!isWebhookConfigValid(config)}
            />
        </Form>
    );
};
