// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { API_URLS } from '@geti/core';
import { useQueryErrorResetBoundary } from '@tanstack/react-query';
import { AxiosError, isAxiosError } from 'axios';
import { StatusCodes } from 'http-status-codes';
import { isRouteErrorResponse, useNavigate, useRouteError } from 'react-router-dom';

import { ErrorFallback } from './error-boundary.component';
import { InvalidOrganizationsScreen } from './invalid-organization/invalid-organization-screen.component';

const getErrorType = (error: unknown): string => {
    if (isRouteErrorResponse(error)) {
        return error.data.error?.message || error.statusText;
    }

    if (isAxiosError(error)) {
        const contentType = error.response?.headers?.['content-type'];
        const responseURL = error.request?.responseURL;

        if (contentType?.includes('text/html') && responseURL?.includes('/dex/auth/')) {
            return StatusCodes.SERVICE_UNAVAILABLE.toString();
        }

        return error.response?.status.toString() ?? error.message;
    }

    if ('message' in (error as AxiosError)) {
        return (error as AxiosError).message;
    }

    if (typeof error === 'string') {
        return error;
    }

    return 'Unknown error';
};

export const RouterErrorBoundary = () => {
    const error = useRouteError();
    const navigate = useNavigate();
    const { reset } = useQueryErrorResetBoundary();

    const resetErrorBoundary = () => {
        // Go back one page in history
        reset();
        navigate(-1);
    };

    if (
        isAxiosError(error) &&
        error.status === StatusCodes.UNAUTHORIZED &&
        error.request.responseURL.endsWith(API_URLS.USER_PROFILE)
    ) {
        return <InvalidOrganizationsScreen />;
    }

    const errorType = getErrorType(error);

    return (
        <ErrorFallback error={{ name: 'router-error', message: errorType }} resetErrorBoundary={resetErrorBoundary} />
    );
};
