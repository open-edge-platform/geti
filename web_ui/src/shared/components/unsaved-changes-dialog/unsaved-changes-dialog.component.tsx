// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
