// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
