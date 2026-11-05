// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { toast } from '@/components/toast/toast.component';
import { useTranslation } from '@/i18n';
import { useQueryClient } from '@tanstack/react-query';

import { getErrorMessage, getQueryKey } from '../../../../query-client/query-client';
import { testSinkQueryOptions } from './use-test-sink';

export const useUpdateSink = () => {
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    return $api.useMutation('patch', '/api/sinks/{sink_id}', {
        meta: {
            invalidateQueries: [['get', '/api/sinks']],
            error: {
                notify: () => false,
            },
        },
        onSuccess: ({ id }, { params: { path } }) => {
            toast({ type: 'success', message: t('inference.sinks.form.updateSuccess') });

            void queryClient.fetchQuery({ ...testSinkQueryOptions(String(id)), staleTime: 0 }).catch(() => undefined);

            return queryClient.invalidateQueries({
                queryKey: getQueryKey(['get', '/api/sinks/{sink_id}', { params: { path: { sink_id: path.sink_id } } }]),
            });
        },
        onError: (error: unknown) => {
            toast({
                type: 'error',
                message: t('inference.sinks.form.saveError', {
                    details: getErrorMessage(error) ?? t('inference.connection.saveErrorFallback'),
                }),
            });
        },
    });
};
