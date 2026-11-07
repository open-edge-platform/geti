// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { toast } from '@/components/toast/toast.component';
import { useTranslation } from '@/i18n';
import { useQueryClient } from '@tanstack/react-query';

import { getErrorMessage } from '../../../../query-client/query-client';
import { testSourceQueryOptions } from './use-test-source';

export const useCreateSource = () => {
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    return $api.useMutation('post', '/api/sources', {
        meta: {
            invalidateQueries: [['get', '/api/sources']],
            error: {
                notify: () => false,
            },
        },
        onSuccess: ({ id }) => {
            toast({ type: 'success', message: t('inference.sources.form.createSuccess') });

            void queryClient.fetchQuery({ ...testSourceQueryOptions(String(id)), staleTime: 0 }).catch(() => undefined);
        },
        onError: (error) => {
            toast({
                type: 'error',
                message: t('inference.sources.form.saveError', {
                    details: getErrorMessage(error) ?? t('inference.connection.saveErrorFallback'),
                }),
            });
        },
    });
};
