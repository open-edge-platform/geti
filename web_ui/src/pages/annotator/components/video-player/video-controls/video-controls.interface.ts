// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface VideoControls {
    canSelectPrevious: boolean;
    previous: () => void;
    canSelectNext: boolean;
    isPlaying: boolean;
    next: () => void;
    play?: () => void;
    pause?: () => void;
    goto: (frameNumber: number) => void;
    canPlay?: boolean;
}
