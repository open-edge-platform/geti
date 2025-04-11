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

import { useQueryErrorResetBoundary } from '@tanstack/react-query';
import { AxiosError, isAxiosError } from 'axios';
import { StatusCodes } from 'http-status-codes';
import { isRouteErrorResponse, useNavigate, useRouteError } from 'react-router-dom';

import { API_URLS } from '../../core/services/urls';
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
