// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { toast } from '@/components/toast/toast.component';
import { useTranslation } from '@/i18n';
import { useQueryClient } from '@tanstack/react-query';

import { getErrorMessage, getQueryKey } from '../../../../query-client/query-client';
import { testSourceQueryOptions } from './use-test-source';

export const useUpdateSource = () => {
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    return $api.useMutation('patch', '/api/sources/{source_id}', {
        meta: {
            invalidateQueries: [['get', '/api/sources']],
            error: {
                notify: () => false,
            },
        },
        onSuccess: ({ id }, { params: { path } }) => {
            toast({ type: 'success', message: t('inference.sources.form.updateSuccess') });

            void queryClient.invalidateQueries({
                queryKey: getQueryKey(['get', '/api/sources/{source_id}', { params: { path } }]),
            });
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
