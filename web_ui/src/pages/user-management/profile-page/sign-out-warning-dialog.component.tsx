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
