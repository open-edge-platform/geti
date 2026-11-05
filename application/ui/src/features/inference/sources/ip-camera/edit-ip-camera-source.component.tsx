// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState, type FormEvent } from 'react';

import type { IPCameraSourceConfig } from '@/api/types';
import { Form } from '@geti-ui/ui';
import { isEqual } from 'lodash-es';

import { useConnectSourceToPipeline } from '../../../../hooks/api/pipeline.hook';
import { useUpdateSource } from '../api/use-update-source';
import { EditSourceButtons } from '../edit-source/edit-source-buttons.component';
import { EditSourceFieldsPanel } from '../edit-source/edit-source-fields-panel.component';
import { EditSourceHeader } from '../edit-source/edit-source-header.component';
import type { EditSourceProps } from '../types';
import { IpCameraFields } from './ip-camera-fields.component';

export const EditIpCameraSource = ({
    source,
    isConnected,
    onSaved,
    onBackToList,
}: EditSourceProps<IPCameraSourceConfig>) => {
    const [config, setConfig] = useState<IPCameraSourceConfig>(source);
    const connectOnSave = useRef(false);
    const updateSource = useUpdateSource();
    const connectSource = useConnectSourceToPipeline();

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();

        try {
            const { id, source_type, ...body } = config;
            await updateSource.mutateAsync({ params: { path: { source_id: id } }, body });
            if (connectOnSave.current) await connectSource.mutateAsync(id);
            onSaved();
        } catch {
            // toasts are handled by the hooks / MutationCache
        }
    };

    return (
        <Form validationBehavior='native' onSubmit={handleSubmit}>
            <EditSourceHeader onBack={onBackToList} />
            <EditSourceFieldsPanel>
                <IpCameraFields value={config} onChange={setConfig} />
            </EditSourceFieldsPanel>
            <EditSourceButtons
                isDisabled={isEqual(config, source)}
                isPending={updateSource.isPending || connectSource.isPending}
                isConnected={isConnected}
                onSave={() => (connectOnSave.current = false)}
                onSaveAndConnect={() => (connectOnSave.current = true)}
            />
        </Form>
    );
};
