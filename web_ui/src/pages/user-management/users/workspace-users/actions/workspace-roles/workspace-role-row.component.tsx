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
