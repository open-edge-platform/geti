// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render, screen } from '@testing-library/react';
import { AuthProvider, useAuth } from 'react-oidc-context';
import { MemoryRouter as Router } from 'react-router-dom';

import * as SharedUtils from '../../shared/utils';
import { BadRequest } from './bad-request/bad-request.component';
import { ErrorScreen } from './general-error-screen/general-error-screen.component';
import { InternalServerError } from './internal-server-error/internal-server-error.component';
import { LoginErrorScreen } from './login-error/login-error-screen.component';
import { ResourceNotFound } from './resource-not-found/resource-not-found.component';
import { ServiceUnavailable } from './service-unavailable/service-unavailable.component';
import { UnauthenticatedUser } from './unauthenticated-user/unauthenticated-user.component';

jest.mock('react-oidc-context', () => ({
    ...jest.requireActual('react-oidc-context'),
    useAuth: jest.fn(),
}));

describe('Error screens', () => {
    const mockRedirectTo = jest.fn();
    jest.spyOn(SharedUtils, 'redirectTo').mockImplementation(mockRedirectTo);

    describe('General error screen', () => {
        it('renders the general error screen properly', () => {
            render(<ErrorScreen resetErrorBoundary={jest.fn()} errorMessage={'Something went wrong...'} />);

            expect(screen.getByText('An error occurred...')).toBeInTheDocument();
            expect(screen.getByText('Error: Something went wrong...')).toBeInTheDocument();
        });

        it('refreshes the page correctly', () => {
            render(<ErrorScreen resetErrorBoundary={jest.fn()} errorMessage={'Something went wrong...'} />);

            const refreshButton = screen.getByRole('link', { name: 'refreshing' });

            fireEvent.click(refreshButton);

            expect(mockRedirectTo).toHaveBeenCalledWith(window.location.href);
        });

        it('clicking on "go back" reset the error boundary state', () => {
            const mockresetErrorBoundary = jest.fn();

            render(
                <ErrorScreen resetErrorBoundary={mockresetErrorBoundary} errorMessage={'Something went wrong...'} />
            );

            expect(screen.getByText(/Something went wrong.../)).toBeInTheDocument();

            const goBackButton = screen.getByRole('link', { name: 'back' });

            fireEvent.click(goBackButton);

            expect(mockresetErrorBoundary).toHaveBeenCalled();
        });

        it('goes back to home screen route correctly', () => {
            render(<ErrorScreen resetErrorBoundary={jest.fn()} errorMessage={'Something went wrong...'} />);

            const goBackHomeButton = screen.getByRole('link', { name: 'Go back to home' });

            fireEvent.click(goBackHomeButton);

            expect(mockRedirectTo).toHaveBeenCalledWith('/');
        });
    });

    describe('Resource not found', () => {
        it('renders resource unavailable screen correctly', () => {
            render(<ResourceNotFound onReset={jest.fn()} />);

            expect(screen.getByText('Resource not found')).toBeInTheDocument();
        });

        it('refreshes the page correctly', () => {
            const handleReset = jest.fn();
            render(<ResourceNotFound onReset={handleReset} />);

            const refreshButton = screen.getByRole('button', { name: 'Refresh' });

            fireEvent.click(refreshButton);

            expect(mockRedirectTo).toHaveBeenCalledWith(window.location.href);
            expect(handleReset).toHaveBeenCalled();
        });
    });

    describe('Unauthenticated user', () => {
        it('renders unauthenticated user screen correctly', () => {
            render(<UnauthenticatedUser onReset={jest.fn()} />);

            expect(screen.getByText('Unauthenticated')).toBeInTheDocument();
            expect(screen.getByText('Session expired, you probably have logged on other device.')).toBeInTheDocument();
            expect(screen.getByText('Sign in')).toBeInTheDocument();
        });

        it('goes back to home screen route correctly', () => {
            const handleReset = jest.fn();
            render(<UnauthenticatedUser onReset={handleReset} />);

            const signInButton = screen.getByRole('button', { name: 'Sign in' });

            fireEvent.click(signInButton);

            expect(mockRedirectTo).toHaveBeenCalledWith('/');
            expect(handleReset).toHaveBeenCalled();
        });
    });

    describe('Service unavailable', () => {
        it('renders service unavailable screen correctly', () => {
            render(
                <Router>
                    <ServiceUnavailable />
                </Router>
            );

            expect(screen.getByText('We are experiencing technical difficulties')).toBeInTheDocument();
            expect(screen.getByText(/We apologize for the inconvenience/)).toBeInTheDocument();
        });
    });

    describe('Bad request', () => {
        it('renders "bad request" screen correctly', () => {
            render(<BadRequest onReset={jest.fn()} />);

            expect(screen.getByText('The server cannot or will not process the current request.')).toBeInTheDocument();
        });

        it('goes back home correctly', () => {
            const handleReset = jest.fn();
            render(<BadRequest onReset={handleReset} />);

            const goBackHomeButton = screen.getByRole('button', { name: 'Go back to home' });

            fireEvent.click(goBackHomeButton);

            expect(mockRedirectTo).toHaveBeenCalledWith('/');
            expect(handleReset).toHaveBeenCalled();
        });
    });

    describe('InternalServerError', () => {
        it('renders "internal server error" screen correctly', () => {
            render(<InternalServerError onReset={jest.fn()} />);

            expect(
                screen.getByText('The server encountered an error and could not complete your request.')
            ).toBeInTheDocument();
        });

        it('goes back home correctly', () => {
            const handleReset = jest.fn();
            render(<InternalServerError onReset={handleReset} />);

            const goBackHomeButton = screen.getByRole('button', { name: 'Go back to home' });

            fireEvent.click(goBackHomeButton);

            expect(mockRedirectTo).toHaveBeenCalledWith('/');
            expect(handleReset).toHaveBeenCalled();
        });
    });

    describe('Login error', () => {
        afterEach(() => {
            jest.clearAllMocks();
        });

        it('renders general error message', () => {
            jest.mocked(useAuth).mockImplementationOnce(() => ({
                // @ts-expect-error we only care about mocking the 'name' prop
                error: {
                    name: '',
                },
            }));

            render(
                <AuthProvider>
                    <LoginErrorScreen />
                </AuthProvider>
            );

            expect(screen.getByText('An error occurred during login.')).toBeInTheDocument();
        });

        it('renders correct error message based on the type of error', () => {
            jest.mocked(useAuth).mockImplementationOnce(() => ({
                // @ts-expect-error we only care about mocking the 'name' prop
                error: {
                    name: 'UserNotLoggedInError',
                },
            }));

            render(<LoginErrorScreen />);

            expect(screen.getByText('User is not currently logged in.')).toBeInTheDocument();
        });
    });
});
