// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, View } from '@adobe/react-spectrum';
import { QuietActionButton } from '@shared/components/quiet-button/quiet-action-button.component';
import { CTRL_OR_COMMAND_KEY } from '@shared/hotkeys';
import { useHotkeys } from 'react-hotkeys-hook';

import { Redo, Undo } from '../../../../../assets/icons';
import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { UndoRedoActions } from '../../../../annotator/core/undo-redo-actions.interface';
import { EdgeLine } from '../util';
import { HotKeysButton } from './hot-keys-button.component';

interface TemplatePrimaryToolbarProps {
    isHotKeysVisible: boolean;
    undoRedoActions: UndoRedoActions<{
        edges: EdgeLine[];
        points: KeypointNode[];
    }>;
}

const UNDO_KEY = `${CTRL_OR_COMMAND_KEY}+z`;
const REDO_KEY = `${CTRL_OR_COMMAND_KEY}+y`;
const REDO_SECOND_KEY = `${CTRL_OR_COMMAND_KEY}+shift+z`;

export const TemplatePrimaryToolbar = ({ undoRedoActions, isHotKeysVisible }: TemplatePrimaryToolbarProps) => {
    const { undo, canUndo, redo, canRedo } = undoRedoActions;

    useHotkeys(UNDO_KEY, undo, { enabled: canUndo }, [undo]);
    useHotkeys([REDO_KEY, REDO_SECOND_KEY], redo, { enabled: canRedo }, [redo]);

    return (
        <View gridArea={'primaryToolbar'} backgroundColor={'gray-200'} padding={'size-100'}>
            <Flex direction={'column'} gap={'size-50'}>
                <QuietActionButton onPress={undo} aria-label='undo' isDisabled={!canUndo}>
                    <Undo />
                </QuietActionButton>
                <QuietActionButton onPress={redo} aria-label='redo' isDisabled={!canRedo}>
                    <Redo />
                </QuietActionButton>

                <Divider size={'S'} />

                {isHotKeysVisible && <HotKeysButton />}
            </Flex>
        </View>
    );
};
