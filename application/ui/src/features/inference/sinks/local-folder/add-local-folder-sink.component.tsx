// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { FormEvent, useState } from 'react';

import { useTranslation } from '@/i18n';
import { Form } from '@geti-ui/ui';

import { useConnectSinkToPipeline } from '../../../../hooks/api/pipeline.hook';
import { AddSinkButton } from '../add-sink/add-sink-button.component';
import { useCreateSink } from '../api/use-create-sink';
import type { AddSinkProps } from '../types';
import { LocalFolderFields } from './local-folder-fields.component';
import { getLocalFolderInitialConfig, isLocalFolderConfigComplete } from './utils';

export const AddLocalFolderSink = ({ onSaved }: AddSinkProps) => {
    const { t } = useTranslation();
    const [config, setConfig] = useState(() => getLocalFolderInitialConfig(t));
    const createSink = useCreateSink();
    const connectSink = useConnectSinkToPipeline();

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();

        try {
            const { id } = await createSink.mutateAsync({
                body: {
                    name: config.name,
                    sink_type: 'folder',
                    folder_path: config.folder_path,
                    rate_limit: config.rate_limit,
                    output_formats: config.output_formats,
                },
            });
            await connectSink.mutateAsync(id);
            onSaved();
        } catch {
            // toasts are handled by the shared hooks / MutationCache
        }
    };

    return (
        <Form validationBehavior='native' onSubmit={handleSubmit}>
            <LocalFolderFields value={config} onChange={setConfig} />
            <AddSinkButton
                isPending={createSink.isPending || connectSink.isPending}
                isDisabled={!isLocalFolderConfigComplete(config)}
            />
        </Form>
    );
};
