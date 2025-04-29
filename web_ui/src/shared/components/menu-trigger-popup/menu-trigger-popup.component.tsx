// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, Key, ReactNode, SetStateAction, useState } from 'react';

import { AlertDialog, DialogContainer, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { MenuTriggerButton } from '../menu-trigger/menu-trigger-button/menu-trigger-button.component';
import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

const CANCEL = 'Cancel';

interface MenuTriggerPopupProps {
    menuTriggerId?: string;
    question: string;
    items?: string[];
    children?: ReactNode;
    isButtonDisabled?: boolean;
    onPrimaryAction: () => void;
    setDeleteUserDialog?: Dispatch<SetStateAction<boolean>>;
    onOpenChange?: Dispatch<SetStateAction<boolean>>;
    ariaLabel?: string;
}

export const MenuTriggerPopup = ({
    menuTriggerId,
    items,
    onPrimaryAction,
    question,
    setDeleteUserDialog,
    children,
    isButtonDisabled,
    onOpenChange,
    ariaLabel,
}: MenuTriggerPopupProps): JSX.Element => {
    const [dialog, setDialog] = useState<Key>();

    return (
        <>
            {!children && items?.length && (
                <MenuTriggerButton
                    id={menuTriggerId ?? ''}
                    onAction={() => {
                        setDialog('delete');
                        setDeleteUserDialog && setDeleteUserDialog(true);
                    }}
                    onOpenChange={onOpenChange}
                    items={items}
                    isQuiet
                />
            )}
            {!items?.length && children && (
                <TooltipTrigger placement={'bottom'} isDisabled={!ariaLabel}>
                    <QuietActionButton
                        isDisabled={isButtonDisabled}
                        aria-label={ariaLabel}
                        onPress={() => setDialog('delete')}
                    >
                        {children}
                    </QuietActionButton>
                    <Tooltip>{ariaLabel}</Tooltip>
                </TooltipTrigger>
            )}
            <DialogContainer
                onDismiss={() => {
                    setDialog(undefined);
                    setDeleteUserDialog && setDeleteUserDialog(false);
                }}
            >
                {dialog === 'delete' && (
                    <AlertDialog
                        id='alert-dialog-id'
                        title='Delete'
                        variant='destructive'
                        primaryActionLabel='Delete'
                        onPrimaryAction={onPrimaryAction}
                        cancelLabel={CANCEL}
                    >
                        {question}
                    </AlertDialog>
                )}
            </DialogContainer>
        </>
    );
};
