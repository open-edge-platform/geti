// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import get from 'lodash/get';
import isEmpty from 'lodash/isEmpty';
import isFunction from 'lodash/isFunction';
import isNil from 'lodash/isNil';
import throttle from 'lodash/throttle';
import { DetailedError } from 'tus-js-client';

import { isNonEmptyArray } from '../../shared/utils';

// Throttling 1 second to prevent redundant calls
export const UPLOAD_PROGRESS_THROTTLING_TIMEOUT = 1000;

export const getUploadId = (url: string | null) => {
    const uploadUrlParts = url?.split('/');

    return isNonEmptyArray(uploadUrlParts) ? uploadUrlParts[uploadUrlParts.length - 1] : null;
};

export const getTUSErrorMessage = (error: Error | DetailedError): string => {
    if ('originalResponse' in error && error.originalResponse !== null) {
        const originalResponse = error.originalResponse;
        const responseBody = isFunction(originalResponse.getBody) ? JSON.parse(originalResponse.getBody()) : {};
        const message = responseBody.message ?? get(error, 'message');
        return message;
    }

    return get(error, 'message');
};

export const onErrorMessage =
    (handler: (message: string) => void) =>
    (error: Error | DetailedError): void => {
        handler(getTUSErrorMessage(error));
    };

export const throttleProgress =
    <T>(predicate: () => undefined | T) =>
    (handler: (data: T, bytesUploaded: number, bytesTotal: number) => void) =>
        throttle((bytesUploaded: number, bytesTotal: number) => {
            const data = predicate();

            if (!isNil(data) && !isEmpty(data)) {
                handler(data, bytesUploaded, bytesTotal);
            }
        }, UPLOAD_PROGRESS_THROTTLING_TIMEOUT);
