// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { Navigate, Outlet, Route } from 'react-router-dom';

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
import {
    RedirectToOrganizationOverview,
    RedirectToOrganizationOverviewFromUsers,
    RedirectToOrganizationWhenUsersAreNotAccessible,
    RedirectToTheOrganizations,
    RedirectToUserOverview,
} from './intel-admin/redirect.component';

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
