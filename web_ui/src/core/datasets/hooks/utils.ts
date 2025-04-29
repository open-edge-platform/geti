// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AxiosError } from 'axios';
import { StatusCodes } from 'http-status-codes';
import isFunction from 'lodash/isFunction';

import {
    isJobCancel,
    isJobDone,
    isJobFailed,
    isJobSettled,
} from '../../../shared/components/header/jobs-management/utils';
import { JobGeneralProps } from '../../jobs/jobs.interface';
import { getFailedJobMessage } from '../../services/utils';
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
        if (isJobDone(jobResponse)) {
            onSuccess(jobResponse);
        }

        if (isJobFailed(jobResponse)) {
            onError({
                message: getFailedJobMessage(jobResponse),
                response: { status: StatusCodes.NOT_IMPLEMENTED },
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
