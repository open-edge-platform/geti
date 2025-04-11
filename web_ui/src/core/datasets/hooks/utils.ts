// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
