// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';

import { Close } from '../../../../../../assets/icons';
import { USER_ROLE, WorkspaceRole } from '../../../../../../core/users/users.interface';
import { WorkspaceEntity } from '../../../../../../core/workspaces/services/workspaces.interface';
import { ActionButton } from '../../../../../../shared/components/button/button.component';
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
