// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useRef, useState } from 'react';

import type { WebhookSinkConfig } from '@/api/types';
import { Form } from '@geti-ui/ui';
import { isEqual } from 'lodash-es';

import { useConnectSinkToPipeline } from '../../../../hooks/api/pipeline.hook';
import { useUpdateSink } from '../api/use-update-sink';
import { EditSinkButtons } from '../edit-sink/edit-sink-buttons.component';
import { EditSinkFieldsPanel } from '../edit-sink/edit-sink-fields-panel.component';
import { EditSinkHeader } from '../edit-sink/edit-sink-header.component';
import type { EditSinkProps } from '../types';
import { isWebhookConfigValid, toWebhookBody, toWebhookFormState } from './utils';
import { WebhookFields } from './webhook-fields.component';

export const EditWebhookSink = ({ sink, isConnected, onSaved, onBackToList }: EditSinkProps<WebhookSinkConfig>) => {
    const [config, setConfig] = useState(() => toWebhookFormState(sink));
    const connectOnSave = useRef(false);
    const updateSink = useUpdateSink();
    const connectSink = useConnectSinkToPipeline();

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();

        try {
            const { id } = await updateSink.mutateAsync({
                params: { path: { sink_id: sink.id } },
                body: toWebhookBody(config),
            });

            if (connectOnSave.current) {
                await connectSink.mutateAsync(String(id));
            }

            onSaved();
        } catch {
            // toasts are handled by the hooks / MutationCache
        }
    };

    return (
        <>
            <EditSinkHeader onBack={onBackToList} />
            <Form validationBehavior='native' onSubmit={handleSubmit}>
                <EditSinkFieldsPanel>
                    <WebhookFields value={config} onChange={setConfig} />
                </EditSinkFieldsPanel>
                <EditSinkButtons
                    isPending={updateSink.isPending || connectSink.isPending}
                    isDisabled={isEqual(config, toWebhookFormState(sink)) || !isWebhookConfigValid(config)}
                    isConnected={isConnected}
                    onSave={() => (connectOnSave.current = false)}
                    onSaveAndConnect={() => (connectOnSave.current = true)}
                />
            </Form>
        </>
    );
};
