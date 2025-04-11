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

import capitalize from 'lodash/capitalize';
import isEmpty from 'lodash/isEmpty';

import { RESOURCE_TYPE, Role } from '../../../../core/users/users.interface';
import { Workspace } from '../../../../core/workspaces/services/workspaces.interface';
import { CasualCell } from '../../../../shared/components/table/components/casual-cell/casual-cell.component';
import { TableCellProps } from '../../../../shared/components/table/table.interface';

interface WorkspacesRoleCellProps extends Omit<TableCellProps, 'cellData'> {
    workspaceId: string | undefined;
    workspaces: Workspace[];
    cellData: Role[];
}

export const WorkspacesRoleCell = ({
    cellData,
    workspaceId,
    workspaces,
    ...rest
}: WorkspacesRoleCellProps): JSX.Element => {
    const workspaceRoles = cellData.filter((role) => role.resourceType === RESOURCE_TYPE.WORKSPACE);

    const selectedWorkspaceRoles = capitalize(workspaceRoles.find((role) => role.resourceId === workspaceId)?.role);
    const availableWorkspaces = workspaceRoles
        .map((role) => workspaces.find((workspace) => workspace.id === role.resourceId)?.name ?? role.resourceId)
        .join(', ');

    const rolesWorkspacesCellData = !isEmpty(workspaceId) ? selectedWorkspaceRoles : availableWorkspaces;

    return <CasualCell {...rest} cellData={rolesWorkspacesCellData} />;
};
