// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { AlertDialog, DialogContainer } from '@adobe/react-spectrum';

interface DeleteUserDialogProps {
    name: string;
    onCancel: () => void;
    isOpen: boolean;
}

export const DeleteUserDialog: FC<DeleteUserDialogProps> = ({ name, onCancel, isOpen }) => {
    const handleDeleteUser = () => {};

    return (
        <DialogContainer onDismiss={onCancel}>
            {isOpen && (
                <AlertDialog
                    title={'Delete'}
                    primaryActionLabel={'Delete'}
                    variant={'destructive'}
                    cancelLabel={'Cancel'}
                    onPrimaryAction={handleDeleteUser}
                    onCancel={onCancel}
                >
                    Are you sure you want to delete user {`"${name}"`}?
                </AlertDialog>
            )}
        </DialogContainer>
    );
};
