// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Navigate, Outlet, useParams } from 'react-router-dom';

import { useFeatureFlags } from '../../core/feature-flags/hooks/use-feature-flags.hook';
import { paths } from './../../core/services/routes';

export const RedirectToTheOrganizations = (): JSX.Element => {
    return <Navigate to={paths.intelAdmin.organizations({})} replace />;
};

export const RedirectToOrganizationOverview = (): JSX.Element => {
    const { organizationId } = useParams<{ organizationId: string }>();

    if (!organizationId) {
        return <Navigate to={paths.intelAdmin.organizations({})} replace />;
    }

    return <Navigate to={paths.intelAdmin.organization.overview({ organizationId })} replace />;
};

export const RedirectToOrganizationWhenUsersAreNotAccessible = () => {
    const { FEATURE_FLAG_MANAGE_USERS } = useFeatureFlags();

    if (FEATURE_FLAG_MANAGE_USERS) {
        return <Outlet />;
    }

    return <Navigate to={paths.intelAdmin.organizations({})} replace />;
};

export const RedirectToUserOverview = () => {
    const { userId } = useParams<{ userId: string }>();

    if (userId === undefined) {
        return <Navigate to={paths.intelAdmin.users({})} replace />;
    }

    return <Navigate to={paths.intelAdmin.user.overview({ userId })} replace />;
};

export const RedirectToOrganizationOverviewFromUsers = () => {
    const { organizationId } = useParams<{ organizationId: string }>();
    const { FEATURE_FLAG_MANAGE_USERS } = useFeatureFlags();

    if (!FEATURE_FLAG_MANAGE_USERS && organizationId) {
        return <Navigate to={paths.intelAdmin.organization.overview({ organizationId })} replace />;
    }

    return <Outlet />;
};
