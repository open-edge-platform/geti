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

import { FC } from 'react';

import { AlertDialog, DialogContainer } from '@adobe/react-spectrum';

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
