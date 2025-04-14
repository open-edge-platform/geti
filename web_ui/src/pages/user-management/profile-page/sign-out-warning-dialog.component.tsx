// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactElement } from 'react';

import { AlertDialog, DialogTrigger } from '@adobe/react-spectrum';

interface SignOutWarningDialogProps {
    handleSignOut: () => void;
    button: ReactElement;
}

export const SignOutWarningDialog = ({ handleSignOut, button }: SignOutWarningDialogProps): JSX.Element => {
    return (
        <DialogTrigger>
            {button}
            <AlertDialog
                title='Upload media in progress'
                variant='warning'
                cancelLabel='Cancel'
                primaryActionLabel='Confirm'
                onPrimaryAction={handleSignOut}
            >
                Some of your files are still uploading. All pending uploads will be cancelled with this action. Are you
                sure you want to sign out?
            </AlertDialog>
        </DialogTrigger>
    );
};
