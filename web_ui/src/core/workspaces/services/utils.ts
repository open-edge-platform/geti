// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
