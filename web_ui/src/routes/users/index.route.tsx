// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Navigate } from 'react-router-dom';

import { paths } from '../../core/services/routes';
import { useOrganizationIdentifier } from '../../hooks/use-organization-identifier/use-organization-identifier.hook';

export const UsersRoute = () => {
    const { organizationId } = useOrganizationIdentifier();
    return <Navigate to={paths.account.users.index({ organizationId })} replace />;
};
