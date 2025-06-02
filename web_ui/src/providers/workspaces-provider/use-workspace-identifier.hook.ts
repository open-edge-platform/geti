// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { WorkspaceIdentifier } from '@geti/core/src/workspaces/services/workspaces.interface';
import { useParams } from 'react-router-dom';

import { useOrganizationIdentifier } from '../../hooks/use-organization-identifier/use-organization-identifier.hook';

export const useWorkspaceIdentifier = (): WorkspaceIdentifier => {
    // Use an empty string so that our unit tests won't fail due to react router not being
    // set up properly
    const { organizationId } = useOrganizationIdentifier();
    const { workspaceId = '' } = useParams<Pick<WorkspaceIdentifier, 'workspaceId'>>();

    return useMemo(() => ({ workspaceId, organizationId }), [workspaceId, organizationId]);
};
