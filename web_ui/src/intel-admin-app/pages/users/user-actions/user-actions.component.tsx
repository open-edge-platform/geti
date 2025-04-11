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

import { FC, Key, useState } from 'react';

import { Delete } from '../../../../assets/icons';
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
