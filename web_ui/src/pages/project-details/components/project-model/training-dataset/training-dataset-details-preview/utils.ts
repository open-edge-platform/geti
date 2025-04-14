// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export const checkIfCanSelectPrevious = (selectedFrameNumber: number, frames: number[]) =>
    selectedFrameNumber !== frames[0];

export const checkIfCanSelectNext = (selectedFrameNumber: number, frames: number[]) =>
    selectedFrameNumber !== frames[frames.length - 1];

export const goPrevious = (selectedFrameNumber: number, frames: number[], goto: (frameIndex: number) => void): void => {
    if (checkIfCanSelectPrevious(selectedFrameNumber, frames)) {
        const index = frames.findIndex((frameNumber) => frameNumber === selectedFrameNumber);
        index !== undefined && goto(frames[index - 1]);
    }
};

export const goNext = (selectedFrameNumber: number, frames: number[], goto: (frameIndex: number) => void): void => {
    if (checkIfCanSelectNext(selectedFrameNumber, frames)) {
        const index = frames.findIndex((frameNumber) => frameNumber === selectedFrameNumber);
        index !== undefined && goto(frames[index + 1]);
    }
};
