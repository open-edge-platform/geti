// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { USER_ROLE, WorkspaceRole } from '@geti/core/src/users/users.interface';
import { WorkspaceEntity } from '@geti/core/src/workspaces/services/workspaces.interface';
import { ActionButton, Flex } from '@geti/ui';
import { Close } from '@geti/ui/icons';

import { RolePicker } from '../../../old-project-users/role-picker.component';
import { WorkspacesPicker } from './workspaces-picker.component';

interface WorkspaceRoleProps {
    workspaceRole: WorkspaceRole;
    changeWorkspace: (value: WorkspaceEntity) => void;
    changeRole: (value: WorkspaceRole['role']) => void;
    deleteWorkspaceRole: () => void;
    workspaces: WorkspaceEntity[];
}
export const WorkspaceRoleRow = ({
    workspaceRole,
    deleteWorkspaceRole,
    changeWorkspace,
    changeRole,
    workspaces,
}: WorkspaceRoleProps): JSX.Element => {
    const { workspace, role } = workspaceRole;

    return (
        <Flex alignItems={'end'} gap={'size-200'} key={`${workspace.name}-row`}>
            <WorkspacesPicker
                selectedWorkspace={workspace}
                workspaces={[...workspaces, workspace]}
                changeWorkspace={changeWorkspace}
            />
            <RolePicker
                roles={[USER_ROLE.WORKSPACE_CONTRIBUTOR, USER_ROLE.WORKSPACE_ADMIN]}
                selectedRole={role}
                setSelectedRole={changeRole}
                width={'50%'}
            />
            <ActionButton onPress={deleteWorkspaceRole}>
                <Close />
            </ActionButton>
        </Flex>
    );
};
