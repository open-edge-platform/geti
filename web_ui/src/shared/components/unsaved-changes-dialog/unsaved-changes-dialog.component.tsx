// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CustomAlertDialog } from '../alert-dialog/custom-alert-dialog.component';

interface UnsavedChangesDialogProps {
    open: boolean;
    setOpen: (isOpen: boolean) => void;
    onPrimaryAction: () => void;
}

export const UnsavedChangesDialog = ({ open, setOpen, onPrimaryAction }: UnsavedChangesDialogProps): JSX.Element => (
    <CustomAlertDialog
        open={open}
        setOpen={setOpen}
        onPrimaryAction={onPrimaryAction}
        title={'Unsaved changes'}
        message={'You have unsaved changes. Are you sure you want to leave this page?'}
        primaryActionLabel={'Leave'}
        cancelLabel={'Stay on page'}
    />
);
