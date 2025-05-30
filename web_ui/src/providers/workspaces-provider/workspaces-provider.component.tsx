// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useWorkspacesApi } from '@geti/core/src/workspaces/hooks/use-workspaces.hook';
import { WorkspaceEntity } from '@geti/core/src/workspaces/services/workspaces.interface';

import { useFirstWorkspaceIdentifier } from './use-first-workspace-identifier.hook';

interface UseWorkspacesReturnType {
    workspaceId: WorkspaceEntity['id'];
    workspaces: WorkspaceEntity[];
}

export const useWorkspaces = (): UseWorkspacesReturnType => {
    const { workspaceId, organizationId } = useFirstWorkspaceIdentifier();
    const { useWorkspacesQuery } = useWorkspacesApi(organizationId);
    const { data = [] } = useWorkspacesQuery();

    return {
        workspaceId,
        workspaces: data,
    };
};
