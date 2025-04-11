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

import { Divider, Flex, View } from '@adobe/react-spectrum';
import { useHotkeys } from 'react-hotkeys-hook';

import { Redo, Undo } from '../../../../../assets/icons';
import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { CTRL_OR_COMMAND_KEY } from '../../../../../shared/hotkeys';
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
