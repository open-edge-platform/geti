// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useActionState } from 'react';

import type { SinkConfig } from '@/api/types';
import { isFunction } from 'lodash-es';

import { toast } from '../../../../components/toast/toast.component';
import { i18n } from '../../../../i18n';
import { useSinkMutation } from './use-sink-mutation.hook';

interface useSinkActionProps<T> {
    config: Awaited<T>;
    isNewSink: boolean;
    onSaved?: (sink_id: string) => void;
    bodyFormatter: (formData: FormData) => T;
}

export const useSinkAction = <T extends SinkConfig>({
    config,
    isNewSink,
    onSaved,
    bodyFormatter,
}: useSinkActionProps<T>) => {
    const addOrUpdateSink = useSinkMutation(isNewSink);

    return useActionState<T, FormData>(async (_prevState: T, formData: FormData) => {
        const body = bodyFormatter(formData);

        try {
            const sink_id = await addOrUpdateSink(body);

            toast({
                type: 'success',
                message: i18n.t(isNewSink ? 'inference.sinkCreatedToast' : 'inference.sinkUpdatedToast'),
            });

            isFunction(onSaved) && onSaved(sink_id);

            return { ...body, id: sink_id };
        } catch (error: unknown) {
            const details = (error as { detail?: string })?.detail;

            toast({
                type: 'error',
                message: i18n.t('inference.sinkSaveFailedToast', {
                    detail: details ?? i18n.t('common.pleaseTryAgain'),
                }),
            });
        }

        return body;
    }, config);
};
