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
