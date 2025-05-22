// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AlertDialog, DialogContainer } from '@geti/ui';
import { OverlayTriggerState } from '@react-stately/overlays';

interface DeleteDialogProps {
    name: string;
    title: string;
    onAction: () => void;
    triggerState: OverlayTriggerState;
}

export const DeleteDialog = ({ triggerState, onAction, name, title }: DeleteDialogProps): JSX.Element => {
    return (
        <DialogContainer onDismiss={() => triggerState.close()}>
            {triggerState.isOpen && (
                <AlertDialog
                    title={`Delete ${title}`}
                    variant='destructive'
                    primaryActionLabel='Delete'
                    onPrimaryAction={() => {
                        triggerState.close();
                        onAction();
                    }}
                    cancelLabel={'Cancel'}
                >
                    {`Are you sure you want to delete "${name}"?`}
                </AlertDialog>
            )}
        </DialogContainer>
    );
};
