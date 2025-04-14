// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { StrictMode, Suspense } from 'react';

import { createRoot } from 'react-dom/client';

import { App, IS_ADMIN_BUILD } from './app.component';
import { ApplicationServicesProvider } from './core/services/application-services-provider.component';
import { NotificationProvider } from './notification/notification.component';
import { ErrorBoundary } from './pages/errors/error-boundary.component';
import { AuthProvider } from './providers/auth-provider/auth-provider.component';
import { ProgressiveWebAppProvider } from './providers/progressive-web-app-provider/progressive-web-app-provider.component';
import { QueryClientProvider } from './providers/query-client-provider/query-client-provider.component';
import reportWebVitals from './report-web-vitals';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';
import { IntelBrandedLoading } from './shared/components/loading/intel-branded-loading.component';
import { ThemeProvider } from './theme/theme-provider.component';

const container = document.getElementById('root') as HTMLElement;
const root = createRoot(container);

const inMemory = process.env.REACT_APP_VALIDATION_COMPONENT_TESTS === 'true';

root.render(
    <StrictMode>
        <ProgressiveWebAppProvider>
            <NotificationProvider>
                <QueryClientProvider>
                    {/* The goal of this additional ThemeProvider (the second one in inside the App) is to have proper
                        styles for the ErrorBoundary views that might be triggered by feature flags or deployment config
                    */}
                    <ThemeProvider>
                        <ErrorBoundary>
                            <Suspense fallback={<IntelBrandedLoading />}>
                                <ApplicationServicesProvider useInMemoryEnvironment={inMemory}>
                                    <AuthProvider isAdmin={IS_ADMIN_BUILD}>
                                        <App />
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

serviceWorkerRegistration.register();

reportWebVitals();
