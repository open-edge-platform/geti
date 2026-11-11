// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';
import { toast } from '@/components/toast/toast.component';
import { useTranslation } from '@/i18n';
import { useQueryClient } from '@tanstack/react-query';

import { getErrorMessage } from '../../../../query-client/query-client';
import { testSinkQueryOptions } from './use-test-sink';

export const useCreateSink = () => {
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    return $api.useMutation('post', '/api/sinks', {
        meta: {
            invalidateQueries: [['get', '/api/sinks']],
            error: {
                notify: () => false,
            },
        },
        onSuccess: ({ id }) => {
            toast({ type: 'success', message: t('inference.sinks.form.createSuccess') });

            void queryClient.fetchQuery({ ...testSinkQueryOptions(String(id)), staleTime: 0 }).catch(() => undefined);
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
