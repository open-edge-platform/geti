// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, AlertDialog, DialogContainer, type ActionButtonProps } from '@geti/ui';
import { Delete } from '@geti/ui/icons';
import { OverlayTriggerState } from 'react-stately';

interface DeleteItemButtonProps extends Omit<ActionButtonProps, 'isQuiet'> {
    id: string;
    alertDialogState: OverlayTriggerState;
    onDeleteItem: (id: string) => void;
}

export const DeleteItemButton = ({
    id,
    alertDialogState,
    onDeleteItem,
    ...styleProps
}: DeleteItemButtonProps): JSX.Element => {
    return (
        <>
            <ActionButton isQuiet onPress={alertDialogState.toggle} {...styleProps} aria-label={'delete'}>
                <Delete />
            </ActionButton>

            <DialogContainer onDismiss={alertDialogState.close}>
                {alertDialogState.isOpen && (
                    <AlertDialog
                        title={'Delete photo'}
                        variant={'destructive'}
                        cancelLabel={'Cancel'}
                        primaryActionLabel={'Delete'}
                        onCancel={alertDialogState.close}
                        onPrimaryAction={() => {
                            onDeleteItem(id);
                            alertDialogState.close();
                        }}
                    >
                        Are you sure you want to delete this photo?
                    </AlertDialog>
                )}
            </DialogContainer>
        </>
    );
};
