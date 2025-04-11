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

import { Divider, Flex, Text, ToggleButton, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

import { Redo, Scope, Undo } from '../../../../../assets/icons';
import { VideoFrame } from '../../../../../core/media/video.interface';
import { Controls } from '../../../../../pages/annotator/components/video-player/video-controls/video-controls.component';
import { VideoControls } from '../../../../../pages/annotator/components/video-player/video-controls/video-controls.interface';
import { ActionButton } from '../../../../../shared/components/button/button.component';
import { useDurationText } from '../../../../../shared/hooks/data-format/use-duration-text.hook';
import { useUndoRedo } from '../../../tools/undo-redo/undo-redo-provider.component';

const UndoRedoButtons = (): JSX.Element => {
    const { undo, canUndo, redo, canRedo } = useUndoRedo();

    return (
        <Flex gap='size-100' alignItems='center' justify-content='center'>
            <TooltipTrigger placement={'bottom'}>
                <ActionButton id='undo-button' data-testid='undo-button' onPress={undo} isDisabled={!canUndo} isQuiet>
                    <Undo />
                </ActionButton>
                <Tooltip>Undo</Tooltip>
            </TooltipTrigger>

            <TooltipTrigger placement={'bottom'}>
                <ActionButton id='redo-button' data-testid='redo-button' onPress={redo} isDisabled={!canRedo} isQuiet>
                    <Redo />
                </ActionButton>
                <Tooltip>Redo</Tooltip>
            </TooltipTrigger>
        </Flex>
    );
};

interface VideoNavigationProps {
    isRangeSelectionEnabled: boolean;
    onToggleRangeSelection: (value: boolean) => void;
    videoFrame: VideoFrame;
    videoControls: VideoControls;
}

export const VideoNavigation = ({
    videoFrame,
    videoControls,
    isRangeSelectionEnabled,
    onToggleRangeSelection,
}: VideoNavigationProps) => {
    const currentTimeText = useDurationText(videoFrame.identifier.frameNumber / videoFrame.metadata.fps);
    const durationText = useDurationText(videoFrame.metadata.frames / videoFrame.metadata.fps);

    return (
        <View gridArea='controls'>
            <Flex gap='size-200' alignItems='center'>
                <Controls videoControls={videoControls} />
                <Text>
                    <span id='video-current-frame-number' aria-label='Currently selected frame number'>
                        {currentTimeText}
                    </span>
                    /{durationText}
                </Text>

                <Flex marginStart='auto' gap={'size-100'} alignItems={'center'}>
                    <UndoRedoButtons />
                    <Divider orientation='vertical' size='S' />
                    <TooltipTrigger>
                        <ToggleButton
                            isQuiet
                            isEmphasized
                            isSelected={isRangeSelectionEnabled}
                            onChange={onToggleRangeSelection}
                            aria-label='Range selector'
                        >
                            <Scope />
                        </ToggleButton>
                        <Tooltip>Range selector</Tooltip>
                    </TooltipTrigger>
                </Flex>
            </Flex>
        </View>
    );
};
