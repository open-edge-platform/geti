// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
