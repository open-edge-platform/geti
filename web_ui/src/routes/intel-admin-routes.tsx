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

import { Navigate, Outlet, Route, useParams } from 'react-router-dom';

import { useFeatureFlags } from '../core/feature-flags/hooks/use-feature-flags.hook';
import { paths } from '../core/services/routes';
import { Layout } from '../intel-admin-app/layout/layout.component';
import { OrganizationCreditAccounts } from '../intel-admin-app/pages/organization/organization-credit-accounts.component';
import { OrganizationLayout } from '../intel-admin-app/pages/organization/organization-layout.component';
import { OrganizationOverview } from '../intel-admin-app/pages/organization/organization-overview.component';
import { OrganizationServiceLimits } from '../intel-admin-app/pages/organization/organization-service-limits.component';
import { OrganizationUsers } from '../intel-admin-app/pages/organization/organization-users.component';
import { OrganizationsLayout } from '../intel-admin-app/pages/organizations/organizations-layout.component';
import { UserLayout } from '../intel-admin-app/pages/user/user-layout.component';
import { UserMemberships } from '../intel-admin-app/pages/user/user-memberships.component';
import { UserOverview } from '../intel-admin-app/pages/user/user-overview.component';
import { UsersLayout } from '../intel-admin-app/pages/users/users-layout.component';
import { Notifications } from '../notification/notification.component';
import { RouterErrorBoundary } from '../pages/errors/router-error-boundary.component';
import { AuthProvider } from '../providers/auth-provider/auth-provider.component';
import { AuthenticationLayout } from './auth/auth.layout';
import { LogoutRoute } from './auth/logout.route';

const RedirectToTheOrganizations = (): JSX.Element => {
    return <Navigate to={paths.intelAdmin.organizations({})} replace />;
};

const RedirectToOrganizationOverview = (): JSX.Element => {
    const { organizationId } = useParams<{ organizationId: string }>();

    if (!organizationId) {
        return <Navigate to={paths.intelAdmin.organizations({})} replace />;
    }

    return <Navigate to={paths.intelAdmin.organization.overview({ organizationId })} replace />;
};

const RedirectToOrganizationWhenUsersAreNotAccessible = () => {
    const { FEATURE_FLAG_MANAGE_USERS } = useFeatureFlags();

    if (FEATURE_FLAG_MANAGE_USERS) {
        return <Outlet />;
    }

    return <Navigate to={paths.intelAdmin.organizations({})} replace />;
};

const RedirectToUserOverview = () => {
    const { userId } = useParams<{ userId: string }>();

    if (userId === undefined) {
        return <Navigate to={paths.intelAdmin.users({})} replace />;
    }

    return <Navigate to={paths.intelAdmin.user.overview({ userId })} replace />;
};

const RedirectToOrganizationOverviewFromUsers = () => {
    const { organizationId } = useParams<{ organizationId: string }>();
    const { FEATURE_FLAG_MANAGE_USERS } = useFeatureFlags();

    if (!FEATURE_FLAG_MANAGE_USERS && organizationId) {
        return <Navigate to={paths.intelAdmin.organization.overview({ organizationId })} replace />;
    }

    return <Outlet />;
};

export const intelAdminRoutes = (): JSX.Element => {
    return (
        <Route
            element={
                <AuthProvider isAdmin>
                    <Notifications />
                    <Outlet />
                </AuthProvider>
            }
            errorElement={<RouterErrorBoundary />}
        >
            <Route
                path={paths.intelAdmin.logout.pattern}
                element={<LogoutRoute home={paths.intelAdmin.organizations({})} />}
            />
            <Route element={<AuthenticationLayout />}>
                <Route path={paths.intelAdmin.index.pattern} element={<Layout />}>
                    {/* OIDC callback route */}
                    <Route
                        path={paths.intelAdmin.authProviderCallback.pattern}
                        element={<Navigate to={paths.intelAdmin.organizations({})} />}
                    />

                    <Route index element={<RedirectToTheOrganizations />} />

                    <Route path={paths.intelAdmin.organizations.pattern}>
                        <Route index element={<OrganizationsLayout />} />

                        <Route path={paths.intelAdmin.organization.index.pattern} element={<OrganizationLayout />}>
                            <Route index element={<RedirectToOrganizationOverview />} />
                            <Route
                                path={paths.intelAdmin.organization.overview.pattern}
                                element={<OrganizationOverview />}
                            />
                            <Route
                                path={paths.intelAdmin.organization.creditAccounts.pattern}
                                element={<OrganizationCreditAccounts />}
                            />
                            <Route
                                path={paths.intelAdmin.organization.serviceLimits.pattern}
                                element={<OrganizationServiceLimits />}
                            />

                            <Route
                                path={paths.intelAdmin.organization.users.pattern}
                                element={<RedirectToOrganizationOverviewFromUsers />}
                            >
                                <Route index element={<OrganizationUsers />} />
                            </Route>
                        </Route>
                    </Route>

                    <Route
                        path={paths.intelAdmin.users.pattern}
                        element={<RedirectToOrganizationWhenUsersAreNotAccessible />}
                    >
                        <Route index element={<UsersLayout />} />

                        <Route path={paths.intelAdmin.user.index.pattern} element={<UserLayout />}>
                            <Route index element={<RedirectToUserOverview />} />
                            <Route path={paths.intelAdmin.user.overview.pattern} element={<UserOverview />} />
                            <Route path={paths.intelAdmin.user.memberships.pattern} element={<UserMemberships />} />
                        </Route>
                    </Route>
                </Route>
            </Route>
        </Route>
    );
};
