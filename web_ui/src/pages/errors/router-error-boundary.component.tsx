// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { API_URLS } from '@geti/core';
import { useQueryErrorResetBoundary } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { StatusCodes } from 'http-status-codes';
import { useNavigate, useRouteError } from 'react-router-dom';

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

    return <ErrorFallback error={error as Error} resetErrorBoundary={resetErrorBoundary} />;
};
