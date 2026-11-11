// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useRef, useState } from 'react';

import type { LocalFolderSinkConfig } from '@/api/types';
import { Form } from '@geti-ui/ui';
import { isEqual } from 'lodash-es';

import { useConnectSinkToPipeline } from '../../../../hooks/api/pipeline.hook';
import { useUpdateSink } from '../api/use-update-sink';
import { EditSinkButtons } from '../edit-sink/edit-sink-buttons.component';
import { EditSinkFieldsPanel } from '../edit-sink/edit-sink-fields-panel.component';
import { EditSinkHeader } from '../edit-sink/edit-sink-header.component';
import type { EditSinkProps } from '../types';
import { LocalFolderFields } from './local-folder-fields.component';
import { isLocalFolderConfigComplete } from './utils';

export const EditLocalFolderSink = ({
    sink,
    isConnected,
    onSaved,
    onBackToList,
}: EditSinkProps<LocalFolderSinkConfig>) => {
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
                    folder_path: config.folder_path,
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
                <LocalFolderFields value={config} onChange={setConfig} />
            </EditSinkFieldsPanel>

            <EditSinkButtons
                isPending={updateSink.isPending || connectSink.isPending}
                isDisabled={isEqual(config, sink) || !isLocalFolderConfigComplete(config)}
                isConnected={isConnected}
                onSave={() => (connectOnSave.current = false)}
                onSaveAndConnect={() => (connectOnSave.current = true)}
            />
        </Form>
    );
};
