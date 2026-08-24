// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from 'react';

import { $api } from '@/api';
import { isFunction } from 'lodash-es';

import { toast } from '../../../components/toast/toast.component';
import { i18n } from '../../../i18n';
import { isNonEmptyString } from '../../../shared/util';
import { isInvalidJob, isJobDone, isJobFailed } from '../util';
import { useStreamJobDetail } from './jobs.hook';

type UseImportJobStatusProps = {
    jobId: string | null | undefined;
    onError?: (error?: unknown) => void;
    onSuccess?: () => void;
};

export const useImportJobStatus = ({ jobId, onError, onSuccess }: UseImportJobStatusProps) => {
    useStreamJobDetail(jobId);

    const response = $api.useQuery(
        'get',
        '/api/jobs/{job_id}',
        { params: { path: { job_id: jobId } } },
        {
            enabled: isNonEmptyString(jobId),
        }
    );

    useEffect(() => {
        if (response.isError && isInvalidJob(response.error)) {
            isFunction(onError) && onError(response.error);
            toast({ type: 'error', message: i18n.t('dataset.importErrorDetail', { detail: response.error?.detail }) });
        }
    }, [onError, response.error, response.isError]);

    useEffect(() => {
        if (isJobFailed(response.data)) {
            isFunction(onError) && onError();
            toast({
                type: 'error',
                message: i18n.t('dataset.importErrorMessage', { message: response.data?.message }),
            });
        }
    }, [onError, response.data]);

    useEffect(() => {
        if (isJobDone(response.data)) {
            isFunction(onSuccess) && onSuccess();
        }
    }, [onSuccess, response.data]);

    return response;
};
