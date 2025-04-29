// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { VideoControls as VideoControlsInterface } from './video-controls.interface';

interface GetMockedVideoControlsProps {
    canSelectPrevious: boolean;
    canSelectNext: boolean;
    isPlaying: boolean;
}

export const getMockedVideoControls = ({
    canSelectPrevious = true,
    canSelectNext = true,
    isPlaying = false,
}: Partial<GetMockedVideoControlsProps>): VideoControlsInterface => {
    return {
        canSelectPrevious,
        previous: jest.fn(),
        canSelectNext,
        next: jest.fn(),
        isPlaying,
        play: jest.fn(),
        pause: jest.fn(),
        goto: jest.fn(),
    };
};
