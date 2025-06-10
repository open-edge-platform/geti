// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AxiosError, AxiosResponse, HttpStatusCode } from 'axios';

import { JobStepState } from '../../../../src/core/jobs/jobs.const';
import { getMockedJob, getMockedJobStep } from '../../../../src/test-utils/mocked-items-factory/mocked-jobs';
import {
    FORBIDDEN_MESSAGE,
    getErrorMessageByStatusCode,
    getFailedJobMessage,
    NETWORK_ERROR_MESSAGE,
    UNPROCESSABLE_ENTITY_MESSAGE,
} from './utils';

const SUPPORTED_HTTP_CODES: (HttpStatusCode.UnprocessableEntity | HttpStatusCode.Forbidden)[] = [
    HttpStatusCode.UnprocessableEntity,
    HttpStatusCode.Forbidden,
];
const mapStatusCodeToMessage = {
    [HttpStatusCode.UnprocessableEntity]: UNPROCESSABLE_ENTITY_MESSAGE,
    [HttpStatusCode.Forbidden]: FORBIDDEN_MESSAGE,
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

            expect(getErrorMessageByStatusCode(mockAxiosError)).toEqual(mockAxiosError.response.data.message);
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
