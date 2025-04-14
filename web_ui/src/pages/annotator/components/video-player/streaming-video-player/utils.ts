// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { VideoPaginationOptions } from '../../../../../core/annotations/services/video-pagination-options.interface';
import { Video, VideoFrame } from '../../../../../core/media/video.interface';
import { ANNOTATOR_MODE } from '../../../core/annotation-tool-context.interface';

const PREDICTIONS_PER_SECOND = 5;

export const getAdjustedNeighbourSize = (fps: number, playbackRate: number, neighbourSize: number) => {
    return Math.max(1, Math.max(Math.ceil(fps / (PREDICTIONS_PER_SECOND / playbackRate)), neighbourSize));
};

export const getVideoOptions = (
    video: Video | VideoFrame | undefined,
    frameNumber: number,
    frameSkip: number,
    chunkSize: number
): VideoPaginationOptions => {
    const annotationChunkSize = chunkSize * frameSkip;

    const startFrame = Math.floor(frameNumber / annotationChunkSize) * annotationChunkSize;
    const frames = video?.metadata?.frames ?? 0;
    const endFrame = Math.min(startFrame + annotationChunkSize - 1, frames - 1);

    const options = {
        endFrame,
        startFrame,
        frameSkip: Math.max(1, frameSkip),
    };

    return options;
};

// We only care about loading or success status, if a query for a buffer errors,
// then we will retry it, or ignore it if it fails too many times
export enum BufferStatus {
    SUCCESS = 'success',
    LOADING = 'loading',
}

export type BufferRange = {
    startFrame: number;
    endFrame: number;
    status: BufferStatus;
};

type BufferGroup = {
    frameSkip: number;
    mode: ANNOTATOR_MODE;
    selectedTaskId?: string | null;
};

export type Buffer = BufferGroup & BufferRange;

export const getFilterForGroup = (mode: ANNOTATOR_MODE, frameSkip: number, selectedTaskId: string | null) => {
    return (buffer: Buffer) => {
        if (mode === ANNOTATOR_MODE.ACTIVE_LEARNING) {
            return buffer.frameSkip === frameSkip && buffer.mode === mode;
        }

        return (
            buffer.frameSkip === frameSkip && buffer.mode === mode && buffer.selectedTaskId === (selectedTaskId ?? null)
        );
    };
};

// The backend returns maximally 20 predictions per request
const FRAMES_BUFFER_CHUNK_SIZE = 20;

const getFirstMissingConsequitiveBuffer = (
    videoFrame: VideoFrame,
    buffersForCurrentMode: Buffer[],
    currentBufferIndex: number,
    mode: ANNOTATOR_MODE,
    frameSkip: number,
    selectedTaskId: string | null,
    bufferLength: number
) => {
    // Find the first buffer after the current frame that we haven't loaded yet
    let previousBuffer = buffersForCurrentMode[currentBufferIndex];

    for (let idx = currentBufferIndex + 1; idx < buffersForCurrentMode.length; idx++) {
        const currentBuffer = buffersForCurrentMode[idx];

        if (currentBuffer.startFrame - 1 !== previousBuffer?.endFrame) {
            // There's a "gap" between the two buffers, so we quit here
            break;
        }

        previousBuffer = currentBuffer;
    }

    const startFrame = Math.min(previousBuffer.startFrame + bufferLength);
    const frames = videoFrame.metadata.frames;
    const endFrame = Math.min(previousBuffer.endFrame + bufferLength, frames - 1);

    // Don't return buffers outside of the range of the video player
    if (startFrame >= frames - 1) {
        return undefined;
    }

    return { startFrame, endFrame, mode, status: BufferStatus.LOADING, frameSkip, selectedTaskId };
};

// This utility function determines which predictions the video player should be loading,
// each buffer is grouped into a "chunk" whose size is determined by the frameSkip and the
// FRAMES_CHUNK_SIZE, the amount of video frame predictions the backend can return at a time.
// If no buffer exists that includes the current videoFrame, we return its associated buffer,
// otherwise we try to find the first buffer chunk that hasn't been loaded yet.
export const getNextBuffer = (
    videoFrame: VideoFrame,
    buffers: Buffer[],
    mode: ANNOTATOR_MODE,
    frameSkip: number,
    selectedTaskId: string | null
): Buffer | undefined => {
    if (videoFrame === undefined) {
        return undefined;
    }

    const currentlyLoadingBuffer = buffers.find(({ status }) => status === 'loading');

    // If any buffer is currently loading, then we want to wait until it is finished
    if (currentlyLoadingBuffer) {
        return currentlyLoadingBuffer;
    }

    // Starting from the current video frame's frame index,
    // find the first buffer
    const frameNumber = videoFrame.identifier.frameNumber;
    const options = getVideoOptions(videoFrame, frameNumber, frameSkip, FRAMES_BUFFER_CHUNK_SIZE);

    const buffersForCurrentMode = buffers.filter(getFilterForGroup(mode, frameSkip, selectedTaskId));
    const currentBufferIndex = buffersForCurrentMode.findIndex(
        ({ startFrame, endFrame }) => startFrame === options.startFrame && endFrame === options.endFrame
    );

    // If we have not started fetching the buffer for the current frame, return it
    if (currentBufferIndex === -1) {
        return {
            ...options,
            mode,
            selectedTaskId: ANNOTATOR_MODE.ACTIVE_LEARNING ? null : (selectedTaskId ?? null),
            status: BufferStatus.LOADING,
        };
    }

    const bufferLength = options.endFrame - options.startFrame + 1;
    const buffer = getFirstMissingConsequitiveBuffer(
        videoFrame,
        buffersForCurrentMode,
        currentBufferIndex,
        mode,
        frameSkip,
        selectedTaskId,
        bufferLength
    );

    // Stop buffering if we finished buffering the next 4 buffers
    // This prevents us from sending too many requets when a video is very long
    if (buffer !== undefined) {
        const distance = Math.abs(videoFrame.identifier.frameNumber - buffer.startFrame);
        const lengthOfABuffer = buffer.endFrame - buffer.startFrame;

        if (distance > lengthOfABuffer * 4) {
            return undefined;
        }
    }

    return buffer;
};

export const isFrameInLoadedBuffer =
    (currentFrame: number) =>
    <T extends BufferRange>({ status, startFrame, endFrame }: T): boolean =>
        status === BufferStatus.SUCCESS && startFrame <= currentFrame && endFrame >= currentFrame;
