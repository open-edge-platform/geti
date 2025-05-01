// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, Key, useState } from 'react';

import { ActionMenu } from '@shared/components/action-menu/action-menu.component';

import { Delete, Edit } from '../../../../assets/icons';
import { User } from '../../users/mocked-user';
import { Membership } from '../mocked-memberships';
import { ChangeRoleDialog } from './change-role-dialog.component';
import { RemoveMembershipDialog } from './remove-membership-dialog.component';

enum MembershipMenuActions {
    CHANGE_ROLE = 'Change role',
    REMOVE = 'Remove membership',
}

const ITEMS = [
    { id: MembershipMenuActions.CHANGE_ROLE, name: MembershipMenuActions.CHANGE_ROLE, icon: <Edit /> },
    { id: MembershipMenuActions.REMOVE, name: MembershipMenuActions.REMOVE, icon: <Delete /> },
];

interface MembershipActionsProps {
    membership: Membership;
    user: User;
}

export const MembershipActions: FC<MembershipActionsProps> = ({ membership, user }) => {
    const [isChangeRoleDialogOpen, setIsChangeRoleDialogOpen] = useState<boolean>(false);
    const [isRemoveDialogOpen, setIsRemoveDialogOpen] = useState<boolean>(false);

    const handleAction = (key: Key) => {
        if (key === MembershipMenuActions.REMOVE) {
            setIsRemoveDialogOpen(true);
        } else if (key === MembershipMenuActions.CHANGE_ROLE) {
            setIsChangeRoleDialogOpen(true);
        }
    };

    const handleCloseChangeRoleDialog = () => {
        setIsChangeRoleDialogOpen(false);
    };

    const handleCloseDeleteDialog = () => {
        setIsRemoveDialogOpen(false);
    };

    return (
        <>
            <ActionMenu items={ITEMS} onAction={handleAction} />
            <ChangeRoleDialog
                isOpen={isChangeRoleDialogOpen}
                membership={membership}
                onCancel={handleCloseChangeRoleDialog}
            />
            <RemoveMembershipDialog
                isOpen={isRemoveDialogOpen}
                onCancel={handleCloseDeleteDialog}
                user={user}
                membership={membership}
            />
        </>
    );
};
