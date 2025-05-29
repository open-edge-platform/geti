// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { useWorkspacesApi } from '@geti/core/src/workspaces/hooks/use-workspaces.hook';
import { WorkspaceIdentifier } from '@geti/core/src/workspaces/services/workspaces.interface';
import { useParams } from 'react-router-dom';

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
