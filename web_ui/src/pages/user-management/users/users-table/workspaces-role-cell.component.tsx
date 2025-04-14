// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
