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

import { FC, FormEvent, useState } from 'react';

import { ButtonGroup, Content, Dialog, Divider, Flex, Form, Heading, TextField } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';

import { useFeatureFlags } from '../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useUsers } from '../../../../../core/users/hook/use-users.hook';
import { getRoleCreationPayload, getRoleDeletionPayload } from '../../../../../core/users/services/utils';
import {
    RESOURCE_TYPE,
    RoleResource,
    UpdateRolePayload,
    User,
    USER_ROLE,
    WorkspaceRole,
} from '../../../../../core/users/users.interface';
import { WorkspaceEntity, WorkspaceIdentifier } from '../../../../../core/workspaces/services/workspaces.interface';
import { useWorkspaces } from '../../../../../providers/workspaces-provider/workspaces-provider.component';
import { Button } from '../../../../../shared/components/button/button.component';
import { RolePicker } from '../../old-project-users/role-picker.component';
import { getAvailableRoles } from './roles-validation';
import { UserSummary } from './user-summary.component';
import { mapRolesToWorkspaceRoles } from './workspace-roles/utils';
import { WorkspaceRolesContainer } from './workspace-roles/workspace-roles-container.component';

import classes from './edit-user-dialog.module.scss';

interface EditUserDialogProps extends WorkspaceIdentifier {
    user: User;
    activeUser: User;
    users: User[];
    isSaasEnvironment: boolean;
    closeDialog: () => void;
}

const MAP_WORKSPACE_ROLE_TO_ORGANIZATION_ROLE: Record<
    USER_ROLE.WORKSPACE_CONTRIBUTOR | USER_ROLE.WORKSPACE_ADMIN,
    USER_ROLE.ORGANIZATION_CONTRIBUTOR | USER_ROLE.ORGANIZATION_ADMIN
> = {
    [USER_ROLE.WORKSPACE_CONTRIBUTOR]: USER_ROLE.ORGANIZATION_CONTRIBUTOR,
    [USER_ROLE.WORKSPACE_ADMIN]: USER_ROLE.ORGANIZATION_ADMIN,
} as const;

const RolesSelection: FC<{
    rolesOptions: WorkspaceRole['role'][];
    workspaceRoles: WorkspaceRole[];
    onChangeRoleHandler: (role: WorkspaceRole['role']) => void;
    onChangeWorkspaceRoles: (roles: WorkspaceRole[]) => void;
    workspaces: WorkspaceEntity[];
}> = ({ rolesOptions, workspaceRoles, onChangeRoleHandler, onChangeWorkspaceRoles, workspaces }) => {
    const { FEATURE_FLAG_WORKSPACE_ACTIONS } = useFeatureFlags();
    const shouldUseSimpleRolesPicker = !FEATURE_FLAG_WORKSPACE_ACTIONS && workspaces.length === 1;

    if (isEmpty(rolesOptions) && shouldUseSimpleRolesPicker) {
        return null;
    }

    if (shouldUseSimpleRolesPicker) {
        return (
            <RolePicker
                roles={rolesOptions}
                selectedRole={workspaceRoles[0].role}
                setSelectedRole={onChangeRoleHandler}
            />
        );
    }

    return (
        <WorkspaceRolesContainer
            workspaceRoles={workspaceRoles}
            setWorkspaceRoles={onChangeWorkspaceRoles}
            workspaces={workspaces}
        />
    );
};

export const EditUserDialog = ({
    organizationId,
    workspaceId,
    user,
    activeUser,
    closeDialog,
    isSaasEnvironment,
    users,
}: EditUserDialogProps): JSX.Element => {
    const { workspaces } = useWorkspaces();
    const { useUpdateUser, useUpdateUserRoles, useUpdateMemberRole } = useUsers();
    const updateRoles = useUpdateUserRoles();
    const updateUser = useUpdateUser();
    const updateMemberRole = useUpdateMemberRole();
    const { FEATURE_FLAG_MANAGE_USERS_ROLES } = useFeatureFlags();

    const [firstName, setFirstName] = useState<string>(user.firstName);
    const [lastName, setLastName] = useState<string>(user.lastName);
    const [workspaceRoles, setWorkspaceRoles] = useState<WorkspaceRole[]>(() =>
        mapRolesToWorkspaceRoles(user.roles, workspaces)
    );

    const isAccountOwner = activeUser.id === user.id;
    const rolesOptions = getAvailableRoles({
        activeMember: activeUser,
        members: users,
        workspaceId,
        isAccountOwner,
    });

    const areRolesEqual = isEqual(workspaceRoles, mapRolesToWorkspaceRoles(user.roles, workspaces));
    const isSaveButtonDisabled = isSaasEnvironment
        ? areRolesEqual
        : areRolesEqual && user.firstName === firstName && user.lastName === lastName;

    const changeRoleHandler = (role: WorkspaceRole['role']) => {
        setWorkspaceRoles([
            {
                role,
                workspace: workspaces[0],
            },
        ]);
    };

    const updateUserName = async () => {
        const editedUser: User = {
            ...user,
            firstName,
            lastName,
            roles: workspaceRoles.map((role) => ({
                role: role.role,
                resourceId: role.workspace.id,
                resourceType: RESOURCE_TYPE.WORKSPACE,
            })),
        };

        await updateUser.mutateAsync({
            user: editedUser,
            userId: user.id,
            organizationId,
        });
    };

    const updateUserRoles = async () => {
        const editedRoles: RoleResource[] = workspaceRoles.map((role) => ({
            role: role.role,
            resourceId: role.workspace.id,
            resourceType: RESOURCE_TYPE.WORKSPACE,
        }));

        const oldRoles: UpdateRolePayload[] = user.roles
            .filter(({ resourceType }) => resourceType === RESOURCE_TYPE.WORKSPACE)
            .map((role) => getRoleDeletionPayload(role));
        const roles: UpdateRolePayload[] = editedRoles.map((role) => getRoleCreationPayload(role));

        return updateRoles.mutateAsync({ newRoles: [...oldRoles, ...roles], userId: user.id, organizationId });
    };

    const handleEditUser = async () => {
        const updateRolesPromise = updateUserRoles();

        if (isSaasEnvironment) {
            await updateRolesPromise;
        } else {
            const updateUserPromise = updateUserName();
            await Promise.all([updateRolesPromise, updateUserPromise]);
        }
    };

    const updateMemberName = async () => {
        const editedUser: User = {
            ...user,
            firstName,
            lastName,
            roles: workspaceRoles.map((role) => ({
                role: MAP_WORKSPACE_ROLE_TO_ORGANIZATION_ROLE[role.role],
                resourceId: organizationId,
                resourceType: RESOURCE_TYPE.ORGANIZATION,
            })),
        };

        await updateUser.mutateAsync({
            user: editedUser,
            userId: user.id,
            organizationId,
        });
    };

    const updateMemberRolesPromises = () => {
        return workspaceRoles.map((workspaceRole) =>
            updateMemberRole.mutateAsync({
                organizationId,
                memberId: user.id,
                role: {
                    role: MAP_WORKSPACE_ROLE_TO_ORGANIZATION_ROLE[workspaceRole.role],
                    resourceId: organizationId,
                },
            })
        );
    };

    const handleEditMember = async () => {
        if (isSaasEnvironment && !areRolesEqual) {
            await Promise.all(updateMemberRolesPromises());

            return;
        }

        const editMemberPromises: Promise<void>[] = [];

        if (!areRolesEqual) {
            editMemberPromises.push(...updateMemberRolesPromises());
        }

        if (user.firstName !== firstName || user.lastName !== lastName) {
            editMemberPromises.push(updateMemberName());
        }

        await Promise.all(editMemberPromises);
    };

    const handleOnSubmit = async (event: FormEvent) => {
        event.preventDefault();

        if (FEATURE_FLAG_MANAGE_USERS_ROLES) {
            await handleEditMember();
        } else {
            await handleEditUser();
        }

        closeDialog();
    };

    return (
        <Dialog minHeight='size-3600' isDismissable>
            <Heading id='edit-user-title' UNSAFE_className={classes.editUserTitle}>
                Edit user
            </Heading>
            <Divider />
            <Content>
                <UserSummary user={user} />
                <Form onSubmit={handleOnSubmit}>
                    {/* 48px = gap + size of delete button */}
                    <Flex gap={'size-200'} alignItems={'end'} UNSAFE_style={{ width: 'calc(100% - 48px' }}>
                        <TextField
                            label='First name'
                            id='edit-first-name'
                            width={'100%'}
                            isDisabled={isSaasEnvironment}
                            value={firstName}
                            onChange={setFirstName}
                        />
                        <TextField
                            label='Last name'
                            id='edit-last-name'
                            width={'100%'}
                            isDisabled={isSaasEnvironment}
                            value={lastName}
                            onChange={setLastName}
                        />
                    </Flex>
                    <RolesSelection
                        rolesOptions={rolesOptions}
                        onChangeRoleHandler={changeRoleHandler}
                        onChangeWorkspaceRoles={setWorkspaceRoles}
                        workspaces={workspaces}
                        workspaceRoles={workspaceRoles}
                    />
                    <ButtonGroup align={'end'} marginTop={'size-350'}>
                        <Button variant='secondary' onPress={closeDialog} id={'cancel-edit-user'}>
                            Cancel
                        </Button>
                        <Button
                            id={'save-edit-user'}
                            variant='accent'
                            type={'submit'}
                            isPending={isSaasEnvironment ? updateRoles.isPending : updateUser.isPending}
                            isDisabled={isSaveButtonDisabled}
                        >
                            Save
                        </Button>
                    </ButtonGroup>
                </Form>
            </Content>
        </Dialog>
    );
};
