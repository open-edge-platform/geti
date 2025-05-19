// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactElement, ReactNode, Suspense } from 'react';

import { defaultTheme, Provider as ThemeProvider } from '@adobe/react-spectrum';
import { IntelBrandedLoading } from '@geti/ui';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { AuthProvider } from 'react-oidc-context';
import { MemoryRouter as Router } from 'react-router-dom';

import { CustomFeatureFlags, DEV_FEATURE_FLAGS } from '../core/feature-flags/services/feature-flag-service.interface';
import { AccountStatusDTO } from '../core/organizations/dtos/organizations.interface';
import QUERY_KEYS from '../core/requests/query-keys';
import {
    ApplicationServicesContextProps,
    ApplicationServicesProvider,
} from '../core/services/application-services-provider.component';
import { OnboardingProfile } from '../core/users/services/onboarding-service.interface';
import { NotificationProvider, Notifications } from '../notification/notification.component';
import { TusUploadProvider } from '../providers/tus-upload-provider/tus-upload-provider.component';
import { getMockedWorkspace } from './mocked-items-factory/mocked-workspace';

interface RequiredProvidersProps extends Partial<ApplicationServicesContextProps> {
    children?: ReactNode;
    initialEntries?: string[];
    featureFlags?: CustomFeatureFlags;
    profile?: OnboardingProfile | null;
    queryClient?: QueryClient;
}

const prefilledOrgId = '000000000000000000000001';

const usePrefilledQueryClient = (featureFlags?: CustomFeatureFlags, profile?: OnboardingProfile | null) => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                gcTime: 1000,
            },
        },
    });

    queryClient.setQueryData(QUERY_KEYS.FEATURE_FLAGS, {
        ...DEV_FEATURE_FLAGS,
        ...featureFlags,
    });

    if (profile !== null) {
        queryClient.setQueryData(QUERY_KEYS.USER_ONBOARDING_PROFILE, {
            organizations: [{ id: prefilledOrgId, status: AccountStatusDTO.ACTIVE }],
            hasAcceptedUserTermsAndConditions: true,
            ...profile,
        });
    }

    ['123', 'org-id', 'organization-id', prefilledOrgId].forEach((organizationId) => {
        const workspaceKey = QUERY_KEYS.WORKSPACES(organizationId);

        queryClient.setQueryData(workspaceKey, [
            getMockedWorkspace({ id: 'workspace-1', name: 'Workspace 1' }),
            getMockedWorkspace({ id: 'workspace-2', name: 'Workspace 2' }),
        ]);
    });

    return queryClient;
};

export const RequiredProviders = ({
    children,
    featureFlags,
    initialEntries,
    profile,
    queryClient,
    ...services
}: RequiredProvidersProps): JSX.Element => {
    const prefilledQueryClient = usePrefilledQueryClient(featureFlags, profile);

    return (
        <Suspense fallback={<IntelBrandedLoading />}>
            <Router initialEntries={initialEntries}>
                <AuthProvider>
                    <NotificationProvider>
                        <Notifications />
                        <QueryClientProvider client={queryClient ?? prefilledQueryClient}>
                            <ThemeProvider theme={defaultTheme}>
                                <ApplicationServicesProvider useInMemoryEnvironment {...services}>
                                    <TusUploadProvider>{children}</TusUploadProvider>
                                </ApplicationServicesProvider>
                            </ThemeProvider>
                        </QueryClientProvider>
                    </NotificationProvider>
                </AuthProvider>
            </Router>
        </Suspense>
    );
};

export interface CustomRenderOptions extends RenderOptions {
    services?: Partial<ApplicationServicesContextProps>;
    featureFlags?: CustomFeatureFlags;
    profile?: OnboardingProfile | null;
    initialEntries?: string[];
}

const customRender = (ui: ReactElement, options?: CustomRenderOptions): RenderResult => {
    const services = options?.services;
    const initialEntries = options?.initialEntries;
    const featureFlags = options?.featureFlags;
    const profile = options?.profile;

    const Wrapper = (props: RequiredProvidersProps) => {
        return (
            <RequiredProviders
                {...props}
                featureFlags={featureFlags}
                profile={profile}
                {...services}
                initialEntries={initialEntries}
            />
        );
    };

    return render(ui, { wrapper: Wrapper, ...options });
};

export { customRender as providersRender };
