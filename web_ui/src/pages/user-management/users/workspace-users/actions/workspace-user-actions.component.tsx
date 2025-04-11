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

import { Key, useState } from 'react';

import { DialogContainer } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { Delete, Edit } from '../../../../../assets/icons';
import { AccountStatus } from '../../../../../core/organizations/organizations.interface';
import { isOrganizationAdmin, isWorkspaceContributor } from '../../../../../core/users/user-role-utils';
import { User } from '../../../../../core/users/users.interface';
import { useIsSaasEnv } from '../../../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { useFirstWorkspaceIdentifier } from '../../../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { ActionMenu } from '../../../../../shared/components/action-menu/action-menu.component';
import { MenuAction } from '../../../../../shared/components/action-menu/menu-action.interface';
import { HasPermission } from '../../../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../../../shared/components/has-permission/has-permission.interface';
import { checkStatusFlowValidity } from '../../utils';
import { EditUserDialog } from './edit-user-dialog.component';
import { RemoveUserDialog } from './remove-user-dialog.component';

enum USER_ACTIONS_OPTIONS {
    DELETE = 'Delete',
    EDIT = 'Edit',
}

interface UserActionsProps {
    activeUser: User;
    user: User;
    users: User[];
}

export const WorkspaceUserActions = ({ activeUser, user, users }: UserActionsProps): JSX.Element => {
    const { organizationId, workspaceId } = useFirstWorkspaceIdentifier();
    const isSaasEnvironment = useIsSaasEnv();

    const [action, setAction] = useState<USER_ACTIONS_OPTIONS | undefined>(undefined);

    const onAction = (key: Key) => setAction(key as USER_ACTIONS_OPTIONS);

    const clearAction = () => setAction(undefined);

    const isOwnAccount = user.id === activeUser?.id;
    const isActiveUserOrgAdmin = isOrganizationAdmin(activeUser, organizationId);
    const isActiveMemberWorkspaceContributor = isWorkspaceContributor(activeUser, workspaceId);

    const editAction = {
        id: USER_ACTIONS_OPTIONS.EDIT,
        name: USER_ACTIONS_OPTIONS.EDIT,
        icon: <Edit />,
    };

    const deleteAction = {
        id: USER_ACTIONS_OPTIONS.DELETE,
        name: USER_ACTIONS_OPTIONS.DELETE,
        icon: <Delete />,
    };

    const canContributorEdit = isActiveMemberWorkspaceContributor && isOwnAccount;
    const canEditUserRole = isActiveUserOrgAdmin || canContributorEdit || activeUser.isAdmin;

    const canDeleteUser =
        isActiveUserOrgAdmin &&
        !isActiveMemberWorkspaceContributor &&
        !isOwnAccount &&
        checkStatusFlowValidity(user.status, AccountStatus.DELETED);

    const editActionItem = canEditUserRole ? editAction : undefined;
    const deleteActionItem = canDeleteUser ? deleteAction : undefined;

    const items = [editActionItem, deleteActionItem].filter((item) => !!item) as MenuAction<USER_ACTIONS_OPTIONS>[];

    if (isEmpty(items)) {
        return <></>;
    }

    //Note: specialCondition is used to allow user edit/delete him/herself
    return (
        <HasPermission operations={[OPERATION.MANAGE_USER]} specialCondition={isOwnAccount}>
            <ActionMenu
                items={items}
                id={`${user.id}-user-action-menu`}
                onAction={onAction}
                ariaLabel={`${user.email} action menu`}
            />
            <DialogContainer onDismiss={clearAction}>
                {action === USER_ACTIONS_OPTIONS.DELETE && (
                    <RemoveUserDialog organizationId={organizationId} user={user} activeUser={activeUser} />
                )}
                {action === USER_ACTIONS_OPTIONS.EDIT && (
                    <EditUserDialog
                        organizationId={organizationId}
                        workspaceId={workspaceId}
                        user={user}
                        activeUser={activeUser}
                        closeDialog={clearAction}
                        isSaasEnvironment={isSaasEnvironment}
                        users={users}
                    />
                )}
            </DialogContainer>
        </HasPermission>
    );
};
