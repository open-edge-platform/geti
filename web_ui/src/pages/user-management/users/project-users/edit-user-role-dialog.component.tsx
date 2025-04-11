// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FormEvent, useState } from 'react';

import { ButtonGroup, Content, Dialog, Divider, Form, Heading } from '@adobe/react-spectrum';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { getRoleCreationPayload, getRoleDeletionPayload } from '../../../../core/users/services/utils';
import { isOrganizationAdmin, isWorkspaceAdmin } from '../../../../core/users/user-role-utils';
import { RESOURCE_TYPE, User, USER_ROLE } from '../../../../core/users/users.interface';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { Button } from '../../../../shared/components/button/button.component';
import { RolePicker } from '../old-project-users/role-picker.component';
import { UserSummary } from '../workspace-users/actions/user-summary.component';

interface EditUserRoleDialogProps {
    user: User;
    activeUser: User | undefined;
    dismiss: () => void;
}

export const EditUserRoleDialog = ({ user, activeUser, dismiss }: EditUserRoleDialogProps): JSX.Element => {
    const { useUpdateUserRoles, useUpdateMemberRole } = useUsers();
    const { organizationId, workspaceId, projectId } = useProjectIdentifier();

    const setUserRole = useUpdateUserRoles();
    const updateMemberRole = useUpdateMemberRole();
    const { FEATURE_FLAG_MANAGE_USERS_ROLES } = useFeatureFlags();

    const isActiveUserOrgAdmin = activeUser !== undefined && isOrganizationAdmin(activeUser, organizationId);
    const isActiveUserWorkspaceAdmin = activeUser !== undefined && isWorkspaceAdmin(activeUser, workspaceId);

    /** Note:
     * if active user is org admin or workspace admin -> can add role project manager or project contributor
     * if active user is project manager -> can add role project contributor
     */

    const roles =
        isActiveUserWorkspaceAdmin || isActiveUserOrgAdmin
            ? [USER_ROLE.PROJECT_MANAGER, USER_ROLE.PROJECT_CONTRIBUTOR]
            : [USER_ROLE.PROJECT_CONTRIBUTOR];

    const currentRole = user.roles.find(
        ({ resourceType, resourceId }) => resourceType === RESOURCE_TYPE.PROJECT && resourceId === projectId
    );

    const [selectedRole, setSelectedRole] = useState<USER_ROLE | undefined>(currentRole?.role);

    const isDisabled = selectedRole === undefined;

    const handleUpdateUserRole = () => {
        if (isDisabled) {
            return;
        }

        if (!currentRole) {
            return;
        }

        setUserRole.mutate(
            {
                newRoles: [
                    getRoleDeletionPayload(currentRole),
                    getRoleCreationPayload({
                        role: selectedRole,
                        resourceId: currentRole.resourceId,
                        resourceType: RESOURCE_TYPE.PROJECT,
                    }),
                ],
                organizationId,
                userId: user.id,
            },
            {
                onSuccess: dismiss,
            }
        );
    };

    const handleSubmitEditUser = (event: FormEvent) => {
        event.preventDefault();

        if (!FEATURE_FLAG_MANAGE_USERS_ROLES) {
            handleUpdateUserRole();
        }

        if (selectedRole === undefined) {
            return;
        }

        updateMemberRole.mutate(
            {
                organizationId,
                role: {
                    role: selectedRole,
                    resourceId: projectId,
                },
                memberId: user.id,
            },
            {
                onSuccess: dismiss,
            }
        );
    };

    return (
        <Dialog onDismiss={dismiss}>
            <Heading id='edit-user-title'>Edit user</Heading>
            <Divider />
            <Content>
                <UserSummary user={user} />
                <Form onSubmit={handleSubmitEditUser}>
                    <RolePicker roles={roles} selectedRole={selectedRole} setSelectedRole={setSelectedRole} />
                    <ButtonGroup align={'end'} marginTop={'size-350'}>
                        <Button variant='secondary' onPress={dismiss} id='cancel-add-member'>
                            Cancel
                        </Button>
                        <Button
                            isPending={setUserRole.isPending}
                            variant='accent'
                            type={'submit'}
                            id='save-add-member'
                            isDisabled={isDisabled}
                        >
                            Save
                        </Button>
                    </ButtonGroup>
                </Form>
            </Content>
        </Dialog>
    );
};
