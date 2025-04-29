// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useParams } from 'react-router-dom';

import { useOrganizationsApi } from '../../../../core/organizations/hook/use-organizations-api.hook';

export const useOrganization = () => {
    const { organizationId } = useParams<{ organizationId: string }>();
    const { useGetOrganizationQuery, useUpdateOrganizationMutation } = useOrganizationsApi();
    const updateOrganization = useUpdateOrganizationMutation();
    const { data: organization, error, isLoading: isGetLoading } = useGetOrganizationQuery(organizationId ?? '');

    return {
        organizationId: organizationId ?? '',
        organization,
        updateOrganization,
        error,
        isLoading: isGetLoading || updateOrganization.isPending,
    };
};
