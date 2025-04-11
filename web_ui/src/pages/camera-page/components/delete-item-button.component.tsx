// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { AlertDialog, DialogContainer, SpectrumActionButtonProps } from '@adobe/react-spectrum';
import { OverlayTriggerState } from 'react-stately';

import { Delete } from '../../../assets/icons';
import { QuietActionButton } from '../../../shared/components/quiet-button/quiet-action-button.component';

interface DeleteItemButtonProps extends Omit<SpectrumActionButtonProps, 'isQuiet'> {
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
            <QuietActionButton onPress={alertDialogState.toggle} {...styleProps} aria-label={'delete'}>
                <Delete />
            </QuietActionButton>

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
