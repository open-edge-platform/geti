// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Tooltip, TooltipTrigger } from '@geti/ui';

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
