// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { useParams } from 'react-router-dom';

import { ProjectIdentifier } from '../../core/projects/core.interface';
import { useWorkspaceIdentifier } from '../../providers/workspaces-provider/use-workspace-identifier.hook';

export const useProjectIdentifier = (): ProjectIdentifier => {
    const { organizationId, workspaceId } = useWorkspaceIdentifier();

    const { projectId } = useParams<Pick<ProjectIdentifier, 'projectId'>>() as Pick<ProjectIdentifier, 'projectId'>;

    return useMemo(() => {
        return { organizationId, workspaceId, projectId };
    }, [organizationId, workspaceId, projectId]);
};
