// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

/*
    Error boundaries on Intel® Geti™:

    1) Wrapping the whole <App />, for error that might happens anywhere (e.g. session expired)
    2) Wrapping <Annotator />, in case of any annotator related endpoint failing (e.g /annotations)
    3) We also use the ErrorBoundary in conjunction with react-router (example @ app-routes.component.tsx)

    - We allow the user to refresh, go back, or dismiss the current error boundary screen

*/

import { ReactNode, useState } from 'react';

import { useQueryErrorResetBoundary } from '@tanstack/react-query';
import { isAxiosError, HttpStatusCode } from 'axios';
import { ErrorBoundary as Boundary, FallbackProps } from 'react-error-boundary';
import { isRouteErrorResponse } from 'react-router-dom';

import { AccessDenied } from './access-denied/access-denied.component';
import { BadRequest } from './bad-request/bad-request.component';
import { ErrorLayout } from './error-layout/error-layout.component';
import { ErrorScreen } from './general-error-screen/general-error-screen.component';
import { InternalServerError } from './internal-server-error/internal-server-error.component';
import { ResourceNotFound } from './resource-not-found/resource-not-found.component';
import { ServiceUnavailable } from './service-unavailable/service-unavailable.component';
import { UnauthenticatedUser } from './unauthenticated-user/unauthenticated-user.component';

const getErrorMessage = (error: unknown): string => {
    if (isRouteErrorResponse(error)) {
        return error.data.error?.message || error.statusText;
    }

    if (isAxiosError(error)) {
        return error.message;
    }

    if (typeof error === 'string') {
        return error;
    }

    return 'Unknown error';
};

export const ErrorFallback = ({ error, resetErrorBoundary }: FallbackProps) => {
    const errorMessage = getErrorMessage(error);

    let component = <ErrorScreen errorMessage={errorMessage} resetErrorBoundary={resetErrorBoundary} />;

    if (isAxiosError(error)) {
        const errorStatus = Number(error.response?.status);

        switch (errorStatus) {
            case HttpStatusCode.BadRequest: // 400
                component = <BadRequest onReset={resetErrorBoundary} />;
                break;
            case HttpStatusCode.NotFound: // 404
                component = <ResourceNotFound onReset={resetErrorBoundary} errorMessage={errorMessage} />;
                break;
            case HttpStatusCode.InternalServerError: // 500
                component = <InternalServerError onReset={resetErrorBoundary} />;
                break;
            case HttpStatusCode.ServiceUnavailable: // 503
            case HttpStatusCode.TooManyRequests: // 429
                component = <ServiceUnavailable />;
                break;
            case HttpStatusCode.Unauthorized: // 401
                component = <UnauthenticatedUser onReset={resetErrorBoundary} />;
                break;
            case HttpStatusCode.Forbidden: // 403
                component = <AccessDenied onReset={resetErrorBoundary} />;
                break;
        }
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
