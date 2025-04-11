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
