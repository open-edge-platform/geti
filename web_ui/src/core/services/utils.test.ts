// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { AxiosError, AxiosResponse } from 'axios';
import { StatusCodes } from 'http-status-codes';

import { getMockedJob, getMockedJobStep } from '../../test-utils/mocked-items-factory/mocked-jobs';
import { JobStepState } from '../jobs/jobs.const';
import {
    FORBIDDEN_MESSAGE,
    getErrorMessageByStatusCode,
    getFailedJobMessage,
    NETWORK_ERROR_MESSAGE,
    UNPROCESSABLE_ENTITY_MESSAGE,
} from './utils';

const SUPPORTED_HTTP_CODES: (StatusCodes.UNPROCESSABLE_ENTITY | StatusCodes.FORBIDDEN)[] = [
    StatusCodes.UNPROCESSABLE_ENTITY,
    StatusCodes.FORBIDDEN,
];
const mapStatusCodeToMessage = {
    [StatusCodes.UNPROCESSABLE_ENTITY]: UNPROCESSABLE_ENTITY_MESSAGE,
    [StatusCodes.FORBIDDEN]: FORBIDDEN_MESSAGE,
};

describe('Services utils', () => {
    describe('Axios utils', () => {
        it('returns the error message if it is present', () => {
            const mockAxiosError: AxiosError & {
                response: {
                    data: AxiosResponse['data'];
                    status: number;
                    statusText: string;
                    headers: unknown;
                    config: unknown;
                };
            } = {
                response: {
                    data: {
                        message: 'some message',
                    },
                    status: 200,
                    statusText: '',
                    headers: {},
                    // @ts-expect-error we dont care about config
                    config: {},
                },
                isAxiosError: true,
                toJSON: jest.fn(),
            };

            expect(getErrorMessageByStatusCode(mockAxiosError)).toEqual(
                `Error: ${mockAxiosError.response.data.message}`
            );
        });

        it('returns the respective message base on the error status code', () => {
            const mockAxiosError: AxiosError & {
                response: {
                    data: unknown;
                    status: number;
                    statusText: string;
                    headers: unknown;
                    config: unknown;
                };
            } = {
                response: {
                    data: {},
                    status: 200,
                    statusText: '',
                    headers: {},
                    // @ts-expect-error we dont care about config
                    config: {},
                },
                isAxiosError: true,
                toJSON: jest.fn(),
            };

            SUPPORTED_HTTP_CODES.forEach((statusCode) => {
                mockAxiosError.response.status = statusCode;

                const message = getErrorMessageByStatusCode(mockAxiosError);

                expect(message).toEqual(mapStatusCodeToMessage[statusCode]);
            });
        });

        it('returns "network error" message if the http code is not supported', () => {
            const mockAxiosError: AxiosError<{ message: string; detail?: string }> = {
                response: {
                    // @ts-expect-error we dont care about data response in this case
                    data: [],
                    status: 480,
                    statusText: '',
                    headers: {},
                    // @ts-expect-error we dont care about headers
                    config: {},
                },
                isAxiosError: true,
                toJSON: jest.fn(),
            };

            const message = getErrorMessageByStatusCode(mockAxiosError);

            expect(message).toEqual(NETWORK_ERROR_MESSAGE);
        });
    });

    it('getFailedJobMessage', () => {
        const testMessage = 'test error message';

        const mockJob1 = getMockedJob({
            steps: [getMockedJobStep({ index: 1, state: JobStepState.FAILED, message: testMessage })],
        });
        expect(getFailedJobMessage(mockJob1)).toBe(testMessage);

        const mockJob2 = getMockedJob({
            steps: [getMockedJobStep({ index: 1, state: JobStepState.FAILED, message: '' })],
        });
        expect(getFailedJobMessage(mockJob2)).toBe('Something went wrong. Please try again');

        const mockJob3 = getMockedJob({
            steps: [getMockedJobStep({ index: 1, state: JobStepState.FAILED, message: null })],
        });
        expect(getFailedJobMessage(mockJob3)).toBe('Something went wrong. Please try again');
    });
});
