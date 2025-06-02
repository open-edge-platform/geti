// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AxiosError, AxiosResponse, HttpStatusCode } from 'axios';
import { get } from 'lodash-es';

import { VideoPaginationOptions } from '../../../../src/core/annotations/services/video-pagination-options.interface';
import { JobGeneralProps } from '../../../../src/core/jobs/jobs.interface';
import { getJobActiveStep } from '../../../../src/core/jobs/utils';
import { AdvancedFilterSortingOptions } from '../../../../src/core/media/media-filter.interface';
import { isNonEmptyString } from '../../../../src/shared/utils';

export const NETWORK_ERROR_MESSAGE = 'Network error: Please check your connection and try again';
export const UNPROCESSABLE_ENTITY_MESSAGE = 'Unable to process request';
export const FORBIDDEN_MESSAGE = "You don't have permissions to perform this operation";
export const SERVICE_UNAVAILABLE_MESSAGE =
    "The inference server isn't ready yet to process your request. Please try again.";
export const BAD_REQUEST_MESSAGE = 'The server cannot or will not process the current request due to invalid syntax';
export const INTERNAL_SERVER_ERROR_MESSAGE = 'The server encountered an error and could not complete your request';
export const BAD_GATEWAY_MESSAGE = 'Bad gateway - The server returned an invalid response';
export const GATEWAY_TIMEOUT_MESSAGE = 'Gateway timed out';
export const NOT_FOUND_MESSAGE = 'The server can not find requested resource';
export const CONFLICT_MESSAGE = 'The request conflicts with the current state of the server';

export const getErrorMessage = (error: AxiosError) => {
    const responseMessage: string | undefined = get(error, 'response.data.message');

    return responseMessage || error.message;
};

export const getFailedJobMessage = (
    job: JobGeneralProps,
    message = 'Something went wrong. Please try again'
): string => {
    const activeStep = getJobActiveStep(job);

    return activeStep !== undefined && isNonEmptyString(activeStep?.message) ? activeStep.message : message;
};

export const getErrorMessageByStatusCode = (error: AxiosError): string => {
    const statusCode: number | undefined = get(error, 'response.status');
    const message = (get(error, 'response.data.message') || get(error, 'response.data')) as string | undefined;

    if (message && typeof message === 'string') {
        return `Error: ${message}`;
    }

    switch (statusCode) {
        case HttpStatusCode.UnprocessableEntity:
            // In case of a 422 error response, we need to show a specific message
            // https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/422
            return get(error, 'response.data.detail') || UNPROCESSABLE_ENTITY_MESSAGE;
        case HttpStatusCode.Forbidden:
            return FORBIDDEN_MESSAGE;
        case HttpStatusCode.Conflict:
            return CONFLICT_MESSAGE;
        case HttpStatusCode.BadRequest:
            return BAD_REQUEST_MESSAGE;
        case HttpStatusCode.NotFound:
            return NOT_FOUND_MESSAGE;
        case HttpStatusCode.InternalServerError:
            return INTERNAL_SERVER_ERROR_MESSAGE;
        case HttpStatusCode.BadGateway:
            return BAD_GATEWAY_MESSAGE;
        case HttpStatusCode.GatewayTimeout:
            return GATEWAY_TIMEOUT_MESSAGE;
        case HttpStatusCode.ServiceUnavailable:
        default:
            return NETWORK_ERROR_MESSAGE;
    }
};

export const buildAdvancedFilterSearchOptions = (
    mediaItemsLoadSize: number,
    sortingOptions: AdvancedFilterSortingOptions
): URLSearchParams => {
    const searchOptionsUrl = new URLSearchParams();

    if (sortingOptions.sortBy) {
        searchOptionsUrl.set('sort_by', sortingOptions.sortBy.toLowerCase().replaceAll(' ', '_'));
        searchOptionsUrl.set('sort_direction', sortingOptions.sortDir ?? '');
    }

    searchOptionsUrl.set('limit', mediaItemsLoadSize.toString());

    return searchOptionsUrl;
};

export const addVideoPaginationSearchParams = (
    options: VideoPaginationOptions,
    searchParams: URLSearchParams
): URLSearchParams => {
    searchParams.set('start_frame', `${options.startFrame}`);

    if (options.endFrame) {
        searchParams.set('end_frame', `${options.endFrame}`);
    }

    if (options.frameSkip) {
        searchParams.set('frameskip', `${options.frameSkip}`);
    }

    if (options.labelsOnly) {
        searchParams.set('label_only', `true`);
    }

    return searchParams;
};

export const isAuthenticationResponseUrl = (response?: AxiosResponse) => {
    const { responseURL } = response?.request;
    const contentType = response?.headers['content-type'];

    return (
        response?.status === HttpStatusCode.Unauthorized ||
        (contentType?.includes('text/html') && responseURL?.includes('/dex/auth/'))
    );
};

export const is404Error = (error: AxiosError) => {
    return error?.response?.status === HttpStatusCode.NotFound;
};

export const isAdminLocation = () => {
    return window.location.pathname.startsWith('/intel-admin');
};
