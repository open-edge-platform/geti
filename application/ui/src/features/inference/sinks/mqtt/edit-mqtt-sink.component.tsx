// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useRef, useState } from 'react';

import type { MqttSinkConfig } from '@/api/types';
import { Form } from '@geti-ui/ui';
import { isEqual } from 'lodash-es';

import { useConnectSinkToPipeline } from '../../../../hooks/api/pipeline.hook';
import { useUpdateSink } from '../api/use-update-sink';
import { EditSinkButtons } from '../edit-sink/edit-sink-buttons.component';
import { EditSinkFieldsPanel } from '../edit-sink/edit-sink-fields-panel.component';
import { EditSinkHeader } from '../edit-sink/edit-sink-header.component';
import type { EditSinkProps } from '../types';
import { MqttFields } from './mqtt-fields.component';
import { isMqttConfigComplete } from './utils';

export const EditMqttSink = ({ sink, isConnected, onSaved, onBackToList }: EditSinkProps<MqttSinkConfig>) => {
    const [config, setConfig] = useState(sink);
    const connectOnSave = useRef(false);
    const updateSink = useUpdateSink();
    const connectSink = useConnectSinkToPipeline();

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();

        try {
            const { id } = await updateSink.mutateAsync({
                params: { path: { sink_id: config.id } },
                body: {
                    name: config.name,
                    broker_host: config.broker_host,
                    broker_port: config.broker_port,
                    topic: config.topic,
                    auth_required: config.auth_required,
                    rate_limit: config.rate_limit,
                    output_formats: config.output_formats,
                },
            });

            if (connectOnSave.current) {
                await connectSink.mutateAsync(id);
            }

            onSaved();
        } catch {
            // toasts are handled by the shared hooks / MutationCache
        }
    };

    return (
        <Form validationBehavior='native' onSubmit={handleSubmit}>
            <EditSinkHeader onBack={onBackToList} />

            <EditSinkFieldsPanel>
                <MqttFields value={config} onChange={setConfig} />
            </EditSinkFieldsPanel>

            <EditSinkButtons
                isPending={updateSink.isPending || connectSink.isPending}
                isDisabled={isEqual(config, sink) || !isMqttConfigComplete(config)}
                isConnected={isConnected}
                onSave={() => (connectOnSave.current = false)}
                onSaveAndConnect={() => (connectOnSave.current = true)}
            />
        </Form>
    );
};
