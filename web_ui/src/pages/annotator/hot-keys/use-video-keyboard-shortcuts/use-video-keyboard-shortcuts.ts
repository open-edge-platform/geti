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

import { useHotkeys } from 'react-hotkeys-hook';

import { VideoControls } from '../../components/video-player/video-controls/video-controls.interface';
import { useAnnotatorHotkeys } from '../../hooks/use-hotkeys-configuration.hook';
import { HOTKEY_OPTIONS } from '../utils';

export const useVideoKeyboardShortcuts = (videoControls: VideoControls): void => {
    const { canSelectPrevious, previous, canSelectNext, next, pause, play, isPlaying } = videoControls;
    const { hotkeys } = useAnnotatorHotkeys();

    useHotkeys(hotkeys.previousFrame, previous, { enabled: canSelectPrevious }, [canSelectPrevious, previous]);
    useHotkeys(hotkeys.nextFrame, next, { enabled: canSelectNext }, [canSelectNext, next]);

    useHotkeys(
        hotkeys.playOrPause,
        () => {
            if (isPlaying) {
                pause?.();
            } else {
                play?.();
            }
        },
        { ...HOTKEY_OPTIONS, enabled: true },
        [isPlaying, pause, play]
    );
};
