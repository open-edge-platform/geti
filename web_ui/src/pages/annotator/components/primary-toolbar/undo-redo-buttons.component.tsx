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

import { Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { Flex } from '@react-spectrum/layout';

import { Redo, Undo } from '../../../../assets/icons';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { useUndoRedoKeyboardShortcuts } from '../../hot-keys/use-undo-redo-keyboard-shortcuts/use-undo-redo-keyboard-shortcuts';
import { useUndoRedo } from '../../tools/undo-redo/undo-redo-provider.component';

export const UndoRedoButtons = ({ isDisabled }: { isDisabled: boolean }): JSX.Element => {
    const { undo, canUndo, redo, canRedo } = useUndoRedo();

    useUndoRedoKeyboardShortcuts('undo', canUndo, undo);
    useUndoRedoKeyboardShortcuts('redo', canRedo, redo);
    useUndoRedoKeyboardShortcuts('redoSecond', canRedo, redo);

    return (
        <Flex
            direction='column'
            gap='size-100'
            alignItems='center'
            justify-content='center'
            data-testid='undo-redo-tools'
        >
            <TooltipTrigger placement={'right'}>
                <QuietActionButton
                    id='undo-button'
                    data-testid='undo-button'
                    onPress={undo}
                    aria-label='undo'
                    isDisabled={!canUndo || isDisabled}
                >
                    <Undo />
                </QuietActionButton>
                <Tooltip>Undo</Tooltip>
            </TooltipTrigger>

            <TooltipTrigger placement={'right'}>
                <QuietActionButton
                    id='redo-button'
                    data-testid='redo-button'
                    aria-label='redo'
                    onPress={redo}
                    isDisabled={!canRedo || isDisabled}
                >
                    <Redo />
                </QuietActionButton>
                <Tooltip>Redo</Tooltip>
            </TooltipTrigger>
        </Flex>
    );
};
