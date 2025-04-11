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

import { RESOURCE_TYPE, Role } from '../../../../core/users/users.interface';
import { CasualCell } from '../../../../shared/components/table/components/casual-cell/casual-cell.component';
import { TableCellProps } from '../../../../shared/components/table/table.interface';

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
