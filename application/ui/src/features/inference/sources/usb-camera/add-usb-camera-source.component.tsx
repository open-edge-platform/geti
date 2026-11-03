// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState, type FormEvent } from 'react';

import { useTranslation } from '@/i18n';
import { Flex, Form } from '@geti-ui/ui';
import { useConnectSourceToPipeline } from 'hooks/api/pipeline.hook';

import { AddSourceButton } from '../add-source/add-source-button.component';
import { useCreateSource } from '../api/use-create-source';
import type { AddSourceProps } from '../types';
import { UsbCameraFields } from './usb-camera-fields.component';
import { getUsbCameraInitialConfig, type UsbCameraFormState } from './utils';

export const AddUsbCameraSource = ({ existingNames, onSaved }: AddSourceProps) => {
    const { t } = useTranslation();
    const [config, setConfig] = useState<UsbCameraFormState>(() => getUsbCameraInitialConfig(t, existingNames));
    const createSource = useCreateSource();
    const connectSource = useConnectSourceToPipeline();

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();

        if (config.device_id === null) return;

        try {
            const { id } = await createSource.mutateAsync({
                body: { name: config.name, source_type: 'usb_camera', device_id: config.device_id },
            });
            await connectSource.mutateAsync(String(id));
            onSaved();
        } catch {
            // toasts are handled by the hooks / MutationCache
        }
    };

    return (
        <Form validationBehavior='native' onSubmit={handleSubmit}>
            <Flex gap='size-200' direction='column'>
                <UsbCameraFields value={config} onChange={setConfig} />

                <AddSourceButton
                    isPending={createSource.isPending || connectSource.isPending}
                    isDisabled={config.device_id === null || config.name.trim().length === 0}
                />
            </Flex>
        </Form>
    );
};
