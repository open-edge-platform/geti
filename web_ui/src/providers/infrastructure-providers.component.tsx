// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode, StrictMode, Suspense, useState } from 'react';

import { createBrowserRouter, createRoutesFromElements, RouterProvider, RouterProviderProps } from 'react-router-dom';

import { useFeatureFlags } from '../core/feature-flags/hooks/use-feature-flags.hook';
import { ApplicationServicesProvider } from '../core/services/application-services-provider.component';
import { NotificationProvider } from '../notification/notification.component';
import { ErrorBoundary } from '../pages/errors/error-boundary.component';
import { IntelBrandedLoading } from '../shared/components/loading/intel-branded-loading.component';
import { ThemeProvider } from '../theme/theme-provider.component';
import { AuthProvider } from './auth-provider/auth-provider.component';
import { ProgressiveWebAppProvider } from './progressive-web-app-provider/progressive-web-app-provider.component';
import { QueryClientProvider } from './query-client-provider/query-client-provider.component';

const useInMemoryEnvironment = process.env.REACT_APP_VALIDATION_COMPONENT_TESTS === 'true';

// Context will be used for preloading data
type Context = unknown;

interface InfrastructureProvidersProps {
    routes: Array<(context?: Context) => ReactNode>;
    isAdminBuild?: boolean;
}

type AppProps = Pick<InfrastructureProvidersProps, 'routes'>;

export const App: FC<AppProps> = ({ routes }) => {
    // Load feature flags at the top of the tree leveraging the suspense.
    useFeatureFlags();

    const [router] = useState<RouterProviderProps['router']>(() =>
        createBrowserRouter(createRoutesFromElements(routes.map((routesGroup) => routesGroup())))
    );

    return (
        <ThemeProvider router={router}>
            <RouterProvider router={router} fallbackElement={<IntelBrandedLoading />} />
            <div id='custom-notification'></div>
        </ThemeProvider>
    );
};

export const InfrastructureProviders: FC<InfrastructureProvidersProps> = ({ routes, isAdminBuild = false }) => {
    return (
        <StrictMode>
            <ProgressiveWebAppProvider>
                <NotificationProvider>
                    <QueryClientProvider>
                        {/*
                        The goal of this additional ThemeProvider (the second one in inside the App) is to have proper
                        styles for the ErrorBoundary views that might be triggered by feature flags or deployment config
                        */}
                        <ThemeProvider>
                            <ErrorBoundary>
                                <Suspense fallback={<IntelBrandedLoading />}>
                                    <ApplicationServicesProvider useInMemoryEnvironment={useInMemoryEnvironment}>
                                        <AuthProvider isAdmin={isAdminBuild}>
                                            <App routes={routes} />
                                        </AuthProvider>
                                    </ApplicationServicesProvider>
                                </Suspense>
                            </ErrorBoundary>
                        </ThemeProvider>
                    </QueryClientProvider>
                </NotificationProvider>
            </ProgressiveWebAppProvider>
        </StrictMode>
    );
};
