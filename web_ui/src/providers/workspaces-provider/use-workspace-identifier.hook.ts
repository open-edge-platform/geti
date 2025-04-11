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

import { WorkspaceIdentifier } from '../../core/workspaces/services/workspaces.interface';
import { useOrganizationIdentifier } from '../../hooks/use-organization-identifier/use-organization-identifier.hook';

export const useWorkspaceIdentifier = (): WorkspaceIdentifier => {
    // Use an empty string so that our unit tests won't fail due to react router not being
    // set up properly
    const { organizationId } = useOrganizationIdentifier();
    const { workspaceId = '' } = useParams<Pick<WorkspaceIdentifier, 'workspaceId'>>();

    return useMemo(() => ({ workspaceId, organizationId }), [workspaceId, organizationId]);
};
