// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState, type FormEvent } from 'react';

import { useTranslation } from '@/i18n';
import { Flex, Form } from '@geti-ui/ui';

import { useConnectSourceToPipeline } from '../../../../hooks/api/pipeline.hook';
import { AddSourceButton } from '../add-source/add-source-button.component';
import { useCreateSource } from '../api/use-create-source';
import type { AddSourceProps } from '../types';
import { IpCameraFields } from './ip-camera-fields.component';
import { getIpCameraInitialConfig, type IpCameraFormState } from './utils';

export const AddIpCameraSource = ({ existingNames, onSaved }: AddSourceProps) => {
    const { t } = useTranslation();
    const [config, setConfig] = useState<IpCameraFormState>(() => getIpCameraInitialConfig(t, existingNames));
    const createSource = useCreateSource();
    const connectSource = useConnectSourceToPipeline();

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();

        try {
            const { id } = await createSource.mutateAsync({ body: config });
            await connectSource.mutateAsync(String(id));
            onSaved();
        } catch {
            // toasts are handled by the hooks / MutationCache
        }
    };

    return (
        <Form validationBehavior='native' onSubmit={handleSubmit}>
            <Flex gap={'size-200'} direction={'column'}>
                <IpCameraFields value={config} onChange={setConfig} />
                <AddSourceButton
                    isPending={createSource.isPending || connectSource.isPending}
                    isDisabled={config.name.trim().length === 0 || config.stream_url.trim().length === 0}
                />
            </Flex>
        </Form>
    );
};
