// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AxiosError, HttpStatusCode } from 'axios';
import isFunction from 'lodash-es/isFunction';

import { getFailedJobMessage } from '../../../../packages/core/src/services/utils';
import {
    isJobCancel,
    isJobDone,
    isJobFailed,
    isJobSettled,
} from '../../../shared/components/header/jobs-management/utils';
import { JobGeneralProps } from '../../jobs/jobs.interface';
import { IntervalJobHandlers } from './dataset-import.interface';

export const getIntervalJobHandlers =
    <T extends JobGeneralProps>({
        onSuccess,
        onSettled,
        onError,
        onCancel,
        onCancelOrFailed,
    }: IntervalJobHandlers<T>) =>
    (jobResponse: T) => {
        if (isFunction(onSuccess) && isJobDone(jobResponse)) {
            onSuccess(jobResponse);
        }

        if (isFunction(onError) && isJobFailed(jobResponse)) {
            onError({
                message: getFailedJobMessage(jobResponse),
                response: { status: HttpStatusCode.NotImplemented },
            } as AxiosError);

            isFunction(onCancelOrFailed) && onCancelOrFailed();
        }

        if (isJobCancel(jobResponse)) {
            isFunction(onCancel) && onCancel();

            isFunction(onCancelOrFailed) && onCancelOrFailed();
        }

        if (isJobSettled(jobResponse)) {
            isFunction(onSettled) && onSettled(jobResponse);
        }
    };
