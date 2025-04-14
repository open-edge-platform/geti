// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { useParams } from 'react-router-dom';

import { useWorkspacesApi } from '../../core/workspaces/hooks/use-workspaces.hook';
import { WorkspaceIdentifier } from '../../core/workspaces/services/workspaces.interface';
import { useOrganizationIdentifier } from '../../hooks/use-organization-identifier/use-organization-identifier.hook';

export const useFirstWorkspaceIdentifier = () => {
    const { organizationId } = useOrganizationIdentifier();

    const { useWorkspacesQuery } = useWorkspacesApi(organizationId);
    const { data: workspaces } = useWorkspacesQuery();

    const { workspaceId = workspaces.at(0)?.id } = useParams<Pick<WorkspaceIdentifier, 'workspaceId'>>();

    if (workspaceId === undefined) {
        throw new Error('Undefined workspace id');
    }

    return useMemo(() => ({ workspaceId, organizationId }), [workspaceId, organizationId]);
};
