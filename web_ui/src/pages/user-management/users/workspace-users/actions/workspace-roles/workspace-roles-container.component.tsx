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

import { USER_ROLE, WorkspaceRole } from '../../../../../../core/users/users.interface';
import { WorkspaceEntity } from '../../../../../../core/workspaces/services/workspaces.interface';
import { Button } from '../../../../../../shared/components/button/button.component';
import { useUserRoles } from './user-user-roles.hook';
import { getUpdatedWorkspaceRoles } from './utils';
import { WorkspaceRoleRow } from './workspace-role-row.component';

interface WorkspaceRolesProps {
    workspaceRoles: WorkspaceRole[];
    setWorkspaceRoles: (workspaces: WorkspaceRole[]) => void;
    workspaces: WorkspaceEntity[];
}

export const WorkspaceRolesContainer = ({
    workspaceRoles,
    setWorkspaceRoles,
    workspaces,
}: WorkspaceRolesProps): JSX.Element => {
    const { canAddNewRole, availableWorkspaces } = useUserRoles(workspaces, workspaceRoles);

    const deleteWorkspaceRole = (index: number) => {
        const roles = [...workspaceRoles];

        roles.splice(index, 1);

        setWorkspaceRoles(roles);
    };

    const changeWorkspace = (value: WorkspaceEntity, index: number) => {
        const editedData = { workspace: value, role: workspaceRoles[index].role };

        setWorkspaceRoles(getUpdatedWorkspaceRoles(editedData, index, workspaceRoles));
    };

    const changeRole = (value: WorkspaceRole['role'], index: number) => {
        const editedData = { workspace: workspaceRoles[index].workspace, role: value };

        setWorkspaceRoles(getUpdatedWorkspaceRoles(editedData, index, workspaceRoles));
    };

    const addWorkspaceRole = () => {
        setWorkspaceRoles([...workspaceRoles, { workspace: availableWorkspaces[0], role: USER_ROLE.WORKSPACE_ADMIN }]);
    };

    return (
        <>
            {workspaceRoles.map((workspaceRole, index) => {
                return (
                    <WorkspaceRoleRow
                        key={`${workspaceRole.workspace.id}-${workspaceRole.role}`}
                        workspaceRole={workspaceRole}
                        changeWorkspace={(value) => changeWorkspace(value, index)}
                        changeRole={(value) => changeRole(value, index)}
                        deleteWorkspaceRole={() => deleteWorkspaceRole(index)}
                        workspaces={availableWorkspaces}
                    />
                );
            })}

            <Button variant={'primary'} onPress={addWorkspaceRole} isDisabled={!canAddNewRole} marginTop={'size-175'}>
                Add workspace role
            </Button>
        </>
    );
};
