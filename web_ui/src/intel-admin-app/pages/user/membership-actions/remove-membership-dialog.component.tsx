// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { AlertDialog, DialogContainer } from '@geti/ui';

import { User } from '../../users/mocked-user';
import { Membership } from '../mocked-memberships';

interface RemoveMembershipDialogProps {
    user: User;
    membership: Membership;
    isOpen: boolean;
    onCancel: () => void;
}

export const RemoveMembershipDialog: FC<RemoveMembershipDialogProps> = ({ isOpen, onCancel, user, membership }) => {
    const handleRemoveMembership = (): void => {};

    return (
        <DialogContainer onDismiss={onCancel}>
            {isOpen && (
                <AlertDialog
                    title={'Remove membership'}
                    primaryActionLabel={'Remove membership'}
                    variant={'destructive'}
                    cancelLabel={'Cancel'}
                    onPrimaryAction={handleRemoveMembership}
                    onCancel={onCancel}
                >
                    Are you sure you want to remove {`${user.firstName} ${user.secondName}'s`} membership from{' '}
                    {`"${membership.organizationName}"`}?
                </AlertDialog>
            )}
        </DialogContainer>
    );
};
