// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceDTO, WorkspacesResponseDTO } from '../dtos/workspace.interface';
import { WorkspaceEntity } from './workspaces.interface';

export const getWorkspaceEntity = (workspace: WorkspaceDTO): WorkspaceEntity => {
    const { id, name, createdBy, createdAt, modifiedBy, modifiedAt, organizationId } = workspace;

    return {
        id,
        name,
        createdBy,
        createdAt,
        modifiedBy,
        modifiedAt,
        organizationId,
    };
};

export const getWorkspaceEntityDTO = (workspace: WorkspaceEntity): WorkspaceDTO => {
    const { id, name, createdBy, createdAt, modifiedBy, modifiedAt, organizationId } = workspace;

    return {
        id,
        name,
        createdBy,
        createdAt,
        modifiedBy,
        modifiedAt,
        organizationId,
    };
};

// NOTE: ATM we are not interested in workspaces pagination
export const getWorkspacesEntity = ({ workspaces }: WorkspacesResponseDTO): WorkspaceEntity[] => {
    return workspaces.map(getWorkspaceEntity);
};
