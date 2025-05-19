// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, ButtonGroup, Content, Dialog, DialogContainer, Divider, Heading, Provider } from '@geti/ui';

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
