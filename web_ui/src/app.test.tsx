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

import { Suspense } from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { App } from './app.component';
import { ApplicationServicesProvider } from './core/services/application-services-provider.component';
import { NotificationProvider, Notifications } from './notification/notification.component';
import { ProjectProvider } from './pages/project-details/providers/project-provider/project-provider.component';
import { IntelBrandedLoading } from './shared/components/loading/intel-branded-loading.component';
import { getMockedProjectIdentifier } from './test-utils/mocked-items-factory/mocked-identifiers';
import { ThemeProvider } from './theme/theme-provider.component';

jest.mock('react-oidc-context', () => ({
    ...jest.requireActual('react-oidc-context'),
    useAuth: () => ({
        user: {
            id_token: 'id_token',
            profile: { sub: '123' },
            expired: false,
        },
        isAuthenticated: true,
        activeNavigator: false,
        isLoading: false,
    }),
}));

describe('App component', () => {
    it('renders correctly', async () => {
        const queryClient = new QueryClient();

        render(
            <Suspense fallback={<div>Test</div>}>
                <QueryClientProvider client={queryClient}>
                    <ThemeProvider>
                        <NotificationProvider>
                            <Suspense fallback={<IntelBrandedLoading />}>
                                <ApplicationServicesProvider useInMemoryEnvironment>
                                    <ProjectProvider projectIdentifier={getMockedProjectIdentifier({})}>
                                        <App />
                                    </ProjectProvider>
                                </ApplicationServicesProvider>
                            </Suspense>
                            <Notifications />
                        </NotificationProvider>
                    </ThemeProvider>
                </QueryClientProvider>
            </Suspense>
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));

        const title = await screen.findByLabelText('intel geti');

        expect(title).toBeInTheDocument();
    });
});
