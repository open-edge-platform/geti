// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC, useMemo, useState } from 'react';

import { ButtonGroup, Content, Dialog, Divider, Grid, Heading } from '@adobe/react-spectrum';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { getRoleCreationPayload } from '../../../../core/users/services/utils';
import { RESOURCE_TYPE, User, USER_ROLE } from '../../../../core/users/users.interface';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { Button } from '../../../../shared/components/button/button.component';
import { hasEqualId } from '../../../../shared/utils';
import { RolePicker } from '../old-project-users/role-picker.component';
import { SelectUser } from '../old-project-users/select-user.component';

const useAvailableUsers = (): User[] => {
    const { projectId, workspaceId, organizationId } = useProjectIdentifier();
    const { useGetUsersQuery } = useUsers();

    const { users: workspaceUsers } = useGetUsersQuery(organizationId, {
        resourceType: RESOURCE_TYPE.WORKSPACE,
        resourceId: workspaceId,
    });
    const { users: projectUsers } = useGetUsersQuery(organizationId, {
        resourceType: RESOURCE_TYPE.PROJECT,
        resourceId: projectId,
    });

    // Returns users from the workspace that are not part of the current project
    const availableUsers = useMemo(() => {
        if (workspaceUsers === undefined || projectUsers === undefined) {
            return [];
        }

        return workspaceUsers.filter((user) => {
            return !projectUsers.some(hasEqualId(user.id));
        });
    }, [workspaceUsers, projectUsers]);

    return availableUsers;
};

interface AddUserToProjectDialogProps {
    onClose: () => void;
}

export const AddUserToProjectDialog: FC<AddUserToProjectDialogProps> = ({ onClose }) => {
    const { organizationId, projectId } = useProjectIdentifier();
    const { FEATURE_FLAG_MANAGE_USERS_ROLES } = useFeatureFlags();

    const { useUpdateUserRoles, useUpdateMemberRole } = useUsers();

    const updateUserRoleMutation = useUpdateUserRoles();
    const updateMemberRoleMutation = useUpdateMemberRole();

    const [selectedUser, setSelectedUser] = useState<User | undefined>(undefined);
    const [selectedRole, setSelectedRole] = useState<USER_ROLE | undefined>(undefined);

    /**
     * Workspace admin can add a user as a project manager and contributor
     * Project manager can add a user as a project manager and contributor
     * Project contributor cannot add users to the project
     *
     * Note: Only workspace/project admin can access this component, so we don't need to check
     * if the user is contributor or not.
     */
    const roles = [USER_ROLE.PROJECT_MANAGER, USER_ROLE.PROJECT_CONTRIBUTOR];
    const availableUsers = useAvailableUsers();

    const isDisabled = selectedUser === undefined || selectedRole === undefined;

    const handleAddUser = () => {
        if (isDisabled) {
            return;
        }

        if (!FEATURE_FLAG_MANAGE_USERS_ROLES) {
            updateUserRoleMutation.mutate(
                {
                    userId: selectedUser.id,
                    organizationId,
                    newRoles: [
                        getRoleCreationPayload({
                            resourceId: projectId,
                            resourceType: RESOURCE_TYPE.PROJECT,
                            role: selectedRole,
                        }),
                    ],
                },
                {
                    onSuccess: () => {
                        onClose();
                    },
                }
            );

            return;
        }

        updateMemberRoleMutation.mutate(
            {
                organizationId,
                memberId: selectedUser.id,
                role: {
                    role: selectedRole,
                    resourceId: projectId,
                },
            },
            {
                onSuccess: () => {
                    onClose();
                },
            }
        );
    };

    return (
        <Dialog>
            <Heading id='add-user-title'>Add user</Heading>
            <Divider />
            <Content>
                <Grid>
                    <SelectUser users={availableUsers} selectedUser={selectedUser} setSelectedUser={setSelectedUser} />
                    <RolePicker
                        width={'auto'}
                        roles={roles}
                        selectedRole={selectedRole}
                        setSelectedRole={setSelectedRole}
                    />
                </Grid>
            </Content>
            <ButtonGroup>
                <Button variant='secondary' onPress={onClose} id='cancel-add-user'>
                    Cancel
                </Button>
                <Button
                    isPending={updateUserRoleMutation.isPending}
                    variant='accent'
                    id='save-add-user'
                    onPress={handleAddUser}
                    isDisabled={isDisabled}
                >
                    Add
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};
