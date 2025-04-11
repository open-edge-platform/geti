// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

/*
    Error boundaries on Intel® Geti™:
    
    1) Wrapping the whole <App />, for error that might happens anywhere (e.g. session expired)
    2) Wrapping <Annotator />, in case of any annotator related endpoint failing (e.g /annotations)
    3) We also use the ErrorBoundary in conjunction with react-router (example @ app-routes.component.tsx) 

    - We allow the user to refresh, go back, or dismiss the current error boundary screen

*/

import { ReactNode, useState } from 'react';

import { useQueryErrorResetBoundary } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { StatusCodes } from 'http-status-codes';
import { ErrorBoundary as Boundary, FallbackProps } from 'react-error-boundary';
import { isRouteErrorResponse } from 'react-router-dom';

import { BadRequest } from './bad-request/bad-request.component';
import { ErrorLayout } from './error-layout/error-layout.component';
import { ErrorScreen } from './general-error-screen/general-error-screen.component';
import { InternalServerError } from './internal-server-error/internal-server-error.component';
import { ResourceNotFound } from './resource-not-found/resource-not-found.component';
import { ServiceUnavailable } from './service-unavailable/service-unavailable.component';
import { UnauthenticatedUser } from './unauthenticated-user/unauthenticated-user.component';

export const ErrorFallback = ({ error, resetErrorBoundary }: FallbackProps) => {
    const errorType = Number(error.message);
    let component: JSX.Element | null = <></>;
    let errorMessage = '';

    if (isRouteErrorResponse(error)) {
        errorMessage = error.data.error?.message || error.statusText;
    } else if ('message' in (error as AxiosError)) {
        errorMessage = (error as AxiosError).message;
    } else if (typeof error === 'string') {
        errorMessage = error;
    } else {
        errorMessage = 'Unknown error';
    }

    switch (errorType) {
        case StatusCodes.BAD_REQUEST: // 400
            component = <BadRequest />;
            break;
        case StatusCodes.NOT_FOUND: // 404
            component = <ResourceNotFound />;
            break;
        case StatusCodes.INTERNAL_SERVER_ERROR: // 500
            component = <InternalServerError />;
            break;
        case StatusCodes.SERVICE_UNAVAILABLE: // 503
        case StatusCodes.TOO_MANY_REQUESTS: // 429
            component = <ServiceUnavailable />;
            break;
        case StatusCodes.UNAUTHORIZED: // 401
            component = <UnauthenticatedUser />;
            break;
        default:
            component = <ErrorScreen errorMessage={errorMessage} resetErrorBoundary={resetErrorBoundary} />;
            break;
    }

    return <ErrorLayout resetErrorBoundary={resetErrorBoundary}>{component}</ErrorLayout>;
};

export const ErrorBoundary = ({
    children,
    FallbackComponent = ErrorFallback,
}: {
    children: ReactNode;
    FallbackComponent?: typeof ErrorFallback;
}): JSX.Element => {
    const [inErrorState, setInErrorState] = useState(false);
    const { reset } = useQueryErrorResetBoundary();

    const handleReset = () => {
        reset();
        setInErrorState(false);
    };

    const handleError = (_error: Error, _info: { componentStack: string }) => {
        // TODO: Send the error info to analytics
        setInErrorState(true);
    };

    return (
        <Boundary
            resetKeys={[inErrorState]}
            onReset={handleReset}
            onError={handleError}
            FallbackComponent={FallbackComponent}
        >
            {children}
        </Boundary>
    );
};
