// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useActionState } from 'react';

import type { SourceConfigPayload } from '@/api/types';
import { isFunction } from 'lodash-es';

import { toast } from '../../../../components/toast/toast.component';
import { i18n } from '../../../../i18n';
import { useSourceMutation } from './use-source-mutation.hook';

interface useSourceActionProps<T> {
    config: Awaited<T>;
    isNewSource: boolean;
    onSaved?: (source_id: string) => void;
    bodyFormatter: (formData: FormData) => T;
    prepareFormData?: (formData: FormData) => Promise<void>;
}

export const useSourceAction = <T extends SourceConfigPayload>({
    config,
    isNewSource,
    onSaved,
    bodyFormatter,
    prepareFormData,
}: useSourceActionProps<T>) => {
    const addOrUpdateSource = useSourceMutation(isNewSource);

    return useActionState<T, FormData>(async (prevState: T, formData: FormData) => {
        try {
            await prepareFormData?.(formData);

            const body = bodyFormatter(formData);
            const source_id = await addOrUpdateSource(body);

            toast({
                type: 'success',
                message: i18n.t(isNewSource ? 'inference.sourceCreatedToast' : 'inference.sourceUpdatedToast'),
            });

            isFunction(onSaved) && onSaved(source_id);
            return { ...body, id: source_id };
        } catch (error: unknown) {
            const details = (error as { detail?: string })?.detail;

            toast({
                type: 'error',
                message: i18n.t('inference.sourceSaveFailedToast', {
                    detail: details ?? i18n.t('common.pleaseTryAgain'),
                }),
            });
        }

        return prevState;
    }, config);
};
