// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState, type FormEvent } from 'react';

import type { USBCameraSourceConfig } from '@/api/types';
import { Form } from '@geti-ui/ui';
import { useConnectSourceToPipeline } from 'hooks/api/pipeline.hook';
import { isEqual } from 'lodash-es';

import { useUpdateSource } from '../api/use-update-source';
import { EditSourceButtons } from '../edit-source/edit-source-buttons.component';
import { EditSourceFieldsPanel } from '../edit-source/edit-source-fields-panel.component';
import { EditSourceHeader } from '../edit-source/edit-source-header.component';
import type { EditSourceProps } from '../types';
import { UsbCameraFields } from './usb-camera-fields.component';
import type { UsbCameraFormState } from './utils';

export const EditUsbCameraSource = ({
    source,
    isConnected,
    onSaved,
    onBackToList,
}: EditSourceProps<USBCameraSourceConfig>) => {
    const [config, setConfig] = useState<UsbCameraFormState>(source);
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
                <UsbCameraFields value={config} onChange={setConfig} />
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
