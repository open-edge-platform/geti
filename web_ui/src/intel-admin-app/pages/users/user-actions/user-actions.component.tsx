// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, Key, useState } from 'react';

import { Delete } from '@geti/ui/icons';

import { ActionMenu } from '../../../../shared/components/action-menu/action-menu.component';
import { User } from '../mocked-user';
import { DeleteUserDialog } from './delete-user-dialog.component';

interface UserActionsProps {
    user: User;
}

enum UserMenuActions {
    DELETE = 'Delete',
}

const ITEMS = [{ id: UserMenuActions.DELETE, name: UserMenuActions.DELETE, icon: <Delete /> }];

export const UserActions: FC<UserActionsProps> = ({ user }) => {
    const [isDeleteDialogVisible, setIsDeleteDialogVisible] = useState<boolean>(false);

    const handleAction = (key: Key) => {
        if (key === UserMenuActions.DELETE) {
            setIsDeleteDialogVisible(true);
        }
    };

    const handleCloseDeleteDialog = () => {
        setIsDeleteDialogVisible(false);
    };

    return (
        <>
            <ActionMenu id={'user-actions'} items={ITEMS} onAction={handleAction} />
            <DeleteUserDialog
                name={`${user.firstName} ${user.secondName}`}
                onCancel={handleCloseDeleteDialog}
                isOpen={isDeleteDialogVisible}
            />
        </>
    );
};
