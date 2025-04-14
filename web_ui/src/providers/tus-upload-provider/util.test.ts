// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DetailedError } from 'tus-js-client';

import { delay } from '../../shared/utils';
import { getUploadId, onErrorMessage, throttleProgress, UPLOAD_PROGRESS_THROTTLING_TIMEOUT } from './util';

describe('tus-upload-provider utils', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('getUploadId', () => {
        const uploadId = '123';

        expect(getUploadId(null)).toBe(null);
        expect(getUploadId(`test/long/${uploadId}`)).toBe(uploadId);
    });

    describe('onErrorMessage', () => {
        const mockedHandler = jest.fn();
        const testHandler = onErrorMessage(mockedHandler);

        it('DetailedError', () => {
            const message = 'test';
            testHandler({
                originalResponse: { getBody: () => JSON.stringify({ message }) },
            } as DetailedError);

            expect(mockedHandler).toHaveBeenCalledWith(message);
        });

        it('Error', () => {
            const message = 'test';
            testHandler({ message } as Error);

            expect(mockedHandler).toHaveBeenCalledWith(message);
        });
    });

    describe('throttleProgress', () => {
        const validData = [1, 2, 3];
        const validPredicated = () => validData;
        const mockedHandler = jest.fn();

        it('predicate is falsy', async () => {
            throttleProgress(() => undefined)(mockedHandler)(1, 2);
            await delay(UPLOAD_PROGRESS_THROTTLING_TIMEOUT);

            expect(mockedHandler).not.toHaveBeenCalled();

            throttleProgress(() => null)(mockedHandler)(1, 2);
            await delay(UPLOAD_PROGRESS_THROTTLING_TIMEOUT);

            expect(mockedHandler).not.toHaveBeenCalled();

            throttleProgress(() => false)(mockedHandler)(1, 2);
            await delay(UPLOAD_PROGRESS_THROTTLING_TIMEOUT);

            expect(mockedHandler).not.toHaveBeenCalled();

            throttleProgress(() => ({}))(mockedHandler)(1, 2);
            await delay(UPLOAD_PROGRESS_THROTTLING_TIMEOUT);

            expect(mockedHandler).not.toHaveBeenCalled();
        });

        it('calls hander after UPLOAD_PROGRESS_THROTTLING_TIMEOUT', async () => {
            const onThrottleProgress = throttleProgress(validPredicated)(mockedHandler);
            onThrottleProgress(1, 1);

            await delay(UPLOAD_PROGRESS_THROTTLING_TIMEOUT + 1);
            onThrottleProgress(1, 2);
            onThrottleProgress(1, 3);
            onThrottleProgress(1, 3);

            expect(mockedHandler).toHaveBeenNthCalledWith(2, validData, 1, 2);
        });
    });
});
