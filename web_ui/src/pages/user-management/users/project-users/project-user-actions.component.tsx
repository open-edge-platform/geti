// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { DialogContainer } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { RESOURCE_TYPE, User } from '../../../../core/users/users.interface';
import { useCheckPermission } from '../../../../shared/components/has-permission/has-permission.component';
import { OPERATION_NEW, OPERATION_OLD } from '../../../../shared/components/has-permission/has-permission.interface';
import { MenuTriggerButton } from '../../../../shared/components/menu-trigger/menu-trigger-button/menu-trigger-button.component';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { EditUserRoleDialog } from './edit-user-role-dialog.component';
import { RemoveUserFromProjectDialog } from './remove-user-from-project-dialog.component';

enum USER_ACTIONS_OPTIONS {
    DELETE = 'Delete',
    EDIT = 'Edit',
}

const useActions = (projectId: string, user: User, activeUser: User | undefined): USER_ACTIONS_OPTIONS[] => {
    const { FEATURE_FLAG_WORKSPACE_ACTIONS } = useFeatureFlags();
    const isOwnAccount = user.id === activeUser?.id;

    const canChangePermissions = useCheckPermission(
        FEATURE_FLAG_WORKSPACE_ACTIONS ? [OPERATION_NEW.ADD_USER_TO_PROJECT] : [OPERATION_OLD.ADD_USER_TO_PROJECT],
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
