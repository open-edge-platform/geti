// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
