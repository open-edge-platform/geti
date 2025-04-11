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

import { useState } from 'react';

import { DialogContainer } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { RESOURCE_TYPE, User } from '../../../../core/users/users.interface';
import { useCheckPermission } from '../../../../shared/components/has-permission/has-permission.component';
import { OPERATION } from '../../../../shared/components/has-permission/has-permission.interface';
import { MenuTriggerButton } from '../../../../shared/components/menu-trigger/menu-trigger-button/menu-trigger-button.component';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { EditUserRoleDialog } from './edit-user-role-dialog.component';
import { RemoveUserFromProjectDialog } from './remove-user-from-project-dialog.component';

enum USER_ACTIONS_OPTIONS {
    DELETE = 'Delete',
    EDIT = 'Edit',
}

const useActions = (projectId: string, user: User, activeUser: User | undefined): USER_ACTIONS_OPTIONS[] => {
    const isOwnAccount = user.id === activeUser?.id;

    const canChangePermissions = useCheckPermission(
        [OPERATION.ADD_USER_TO_PROJECT],
        [
            {
                type: RESOURCE_TYPE.PROJECT,
                id: projectId,
            },
        ]
    );

    /** Note:
     * if active user is org admin, workspace admin or project admin ->
     * can add role project admin or project contributor & can delete
     */
    if (canChangePermissions) {
        return [USER_ACTIONS_OPTIONS.EDIT, USER_ACTIONS_OPTIONS.DELETE];
    } else {
        if (isOwnAccount) {
            return [USER_ACTIONS_OPTIONS.DELETE];
        }
        return [];
    }
};

interface UserActionsProps {
    user: User;
    activeUser: User | undefined;
}

export const ProjectUserActions = ({ user, activeUser }: UserActionsProps): JSX.Element => {
    const [action, setAction] = useState<USER_ACTIONS_OPTIONS | undefined>(undefined);
    const {
        projectIdentifier: { projectId },
    } = useProject();

    const dismiss = () => {
        setAction(undefined);
    };

    const items = useActions(projectId, user, activeUser);

    if (isEmpty(items)) {
        return <></>;
    }

    return (
        <>
            <MenuTriggerButton
                id={`user-action-menu-${user.id}`}
                items={items}
                onAction={(key) => setAction(key as USER_ACTIONS_OPTIONS)}
                isQuiet
            />

            <DialogContainer onDismiss={dismiss}>
                {action === USER_ACTIONS_OPTIONS.DELETE.toLocaleLowerCase() && (
                    <RemoveUserFromProjectDialog user={user} activeUser={activeUser} dismiss={dismiss} />
                )}
                {action === USER_ACTIONS_OPTIONS.EDIT.toLocaleLowerCase() && (
                    <EditUserRoleDialog user={user} activeUser={activeUser} dismiss={dismiss} />
                )}
            </DialogContainer>
        </>
    );
};
