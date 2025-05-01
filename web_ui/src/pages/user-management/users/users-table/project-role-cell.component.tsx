// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CasualCell } from '@shared/components/table/components/casual-cell/casual-cell.component';
import { TableCellProps } from '@shared/components/table/table.interface';

import { RESOURCE_TYPE, Role } from '../../../../core/users/users.interface';

interface ProjectRoleCellProps extends Omit<TableCellProps, 'cellData'> {
    roles: Role[];
    projectId: string;
}

export const ProjectRoleCell = ({ roles, projectId, ...rest }: ProjectRoleCellProps): JSX.Element => {
    const projectRoles = roles.filter(
        (role) => role.resourceType === RESOURCE_TYPE.PROJECT && role.resourceId === projectId
    );
    const cellData = projectRoles.map((role) => role.role).join(', ');

    return <CasualCell {...rest} cellData={cellData} />;
};
