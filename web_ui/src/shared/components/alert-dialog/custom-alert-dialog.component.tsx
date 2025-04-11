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

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Heading, Provider } from '@adobe/react-spectrum';

import { Button } from '../button/button.component';

interface CustomAlertDialogProps {
    open: boolean;
    setOpen: (isOpen: boolean) => void;
    onPrimaryAction: () => void;
    title: string;
    primaryActionLabel: string;
    cancelLabel: string;
    message: string;
    isPrimaryActionDisabled?: boolean;
    cancelButtonAriaLabel?: string;
    primaryActionButtonAriaLabel?: string;
    id?: string;
}

export const CustomAlertDialog = ({
    open,
    title,
    message,
    setOpen,
    cancelLabel,
    onPrimaryAction,
    primaryActionLabel,
    isPrimaryActionDisabled,
    cancelButtonAriaLabel,
    primaryActionButtonAriaLabel,
    id,
}: CustomAlertDialogProps): JSX.Element => (
    <Provider isQuiet={false}>
        <DialogContainer
            onDismiss={() => {
                // We don't want to close the dialog on dismiss because this introduces an
                // issue with useHistoryBlock
                // This might be avoidable once https://github.com/adobe/react-spectrum/issues/1773 is fixed
            }}
            isDismissable={false}
        >
            {open && (
                <Dialog role='alertdialog' id={id}>
                    <Heading>{title}</Heading>
                    <Divider />
                    <Content>{message}</Content>
                    <ButtonGroup>
                        <Button variant='secondary' onPress={() => setOpen(false)} aria-label={cancelButtonAriaLabel}>
                            {cancelLabel}
                        </Button>
                        <Button
                            variant='negative'
                            isDisabled={isPrimaryActionDisabled}
                            onPress={onPrimaryAction}
                            aria-label={primaryActionButtonAriaLabel}
                        >
                            {primaryActionLabel}
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    </Provider>
);
