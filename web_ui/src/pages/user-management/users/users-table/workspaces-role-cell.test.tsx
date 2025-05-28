// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RESOURCE_TYPE, USER_ROLE } from '@geti/core/src/users/users.interface';
import { screen } from '@testing-library/react';

import { getMockedUser } from '../../../../test-utils/mocked-items-factory/mocked-users';
import { getMockedWorkspace } from '../../../../test-utils/mocked-items-factory/mocked-workspace';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { USERS_TABLE_COLUMNS } from './users-table.component';
import { WorkspacesRoleCell } from './workspaces-role-cell.component';

describe('WorkspacesRoleCell', () => {
    const roles = [
        {
            role: USER_ROLE.WORKSPACE_ADMIN,
            resourceId: 'workspace-id',
            resourceType: RESOURCE_TYPE.WORKSPACE,
        },
        {
            role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
            resourceId: 'workspace-id-2',
            resourceType: RESOURCE_TYPE.WORKSPACE,
        },
    ];

    const workspaces = [
        getMockedWorkspace({ id: 'workspace-id', name: 'Workspace 1' }),
        getMockedWorkspace({ id: 'workspace-id-2', name: 'Workspace 2' }),
    ];

    it('Show admin role for selected workspace', () => {
        render(
            <WorkspacesRoleCell
                workspaceId={workspaces.at(0)?.id}
                workspaces={workspaces}
                cellData={roles}
                columnIndex={0}
                dataKey={USERS_TABLE_COLUMNS.ROLES}
                rowIndex={0}
                rowData={[getMockedUser({ roles })]}
                isScrolling={false}
            />
        );

        expect(screen.getByTestId('roles')).toHaveTextContent('Admin');
    });

    it('Show contributor role for selected workspace', () => {
        render(
            <WorkspacesRoleCell
                workspaceId={workspaces.at(1)?.id}
                workspaces={workspaces}
                cellData={roles}
                columnIndex={0}
                dataKey={USERS_TABLE_COLUMNS.ROLES}
                rowIndex={0}
                rowData={[getMockedUser({ roles })]}
                isScrolling={false}
            />
        );

        expect(screen.getByTestId('roles')).toHaveTextContent('Contributor');
    });

    it('Show workspaces available for user', () => {
        render(
            <WorkspacesRoleCell
                workspaceId={undefined}
                workspaces={workspaces}
                cellData={roles}
                columnIndex={0}
                dataKey={USERS_TABLE_COLUMNS.ROLES}
                rowIndex={0}
                rowData={[getMockedUser({ roles })]}
                isScrolling={false}
            />
        );

        expect(screen.getByTestId('roles')).toHaveTextContent('Workspace 1, Workspace 2');
    });
});
