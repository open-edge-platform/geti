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

import { useWorkspacesApi } from '../../core/workspaces/hooks/use-workspaces.hook';
import { WorkspaceEntity } from '../../core/workspaces/services/workspaces.interface';
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
