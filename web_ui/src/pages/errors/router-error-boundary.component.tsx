// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { API_URLS } from '@geti/core/src/services/urls';
import { useQueryErrorResetBoundary } from '@tanstack/react-query';
import { AxiosError, isAxiosError } from 'axios';
import { StatusCodes } from 'http-status-codes';
import { isRouteErrorResponse, useNavigate, useRouteError } from 'react-router-dom';

import { ErrorFallback } from './error-boundary.component';
import { InvalidOrganizationsScreen } from './invalid-organization/invalid-organization-screen.component';

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

    let errorMessage: string;

    if (isRouteErrorResponse(error)) {
        errorMessage = error.data.error?.message || error.statusText;
    } else if ('message' in (error as AxiosError)) {
        errorMessage = (error as AxiosError).message;
    } else if (typeof error === 'string') {
        errorMessage = error;
    } else {
        errorMessage = 'Unknown error';
    }

    return (
        <ErrorFallback
            error={{ name: 'router-error', message: errorMessage }}
            resetErrorBoundary={resetErrorBoundary}
        />
    );
};
