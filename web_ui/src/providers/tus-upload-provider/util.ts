// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
