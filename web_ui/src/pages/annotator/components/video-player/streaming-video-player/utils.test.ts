// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { MEDIA_TYPE } from '../../../../../core/media/base-media.interface';
import { getMockedVideoFrameMediaItem } from '../../../../../test-utils/mocked-items-factory/mocked-media';
import { ANNOTATOR_MODE } from '../../../core/annotation-tool-context.interface';
import { Buffer, BufferRange, BufferStatus, getNextBuffer, isFrameInLoadedBuffer } from './utils';

const getVideoFrame = (frameNumber: number) => {
    return getMockedVideoFrameMediaItem({
        identifier: { frameNumber, videoId: 'video', type: MEDIA_TYPE.VIDEO_FRAME },
        metadata: {
            duration: 100,
            fps: 60,
            frameStride: 60,
            frames: 6000,
            width: 100,
            height: 100,
            size: 100,
        },
    });
};

describe('getNextBuffer', () => {
    const FRAMESKIP = 12;
    const CHUNK_SIZE = 20;

    const getBuffer = ({
        startFrame = 0,
        endFrame = startFrame + FRAMESKIP * CHUNK_SIZE - 1,
        status = BufferStatus.LOADING,
    }: Partial<BufferRange>): Buffer => {
        return {
            startFrame,
            endFrame,
            frameSkip: FRAMESKIP,
            status,
            mode: ANNOTATOR_MODE.ACTIVE_LEARNING,
            selectedTaskId: null,
        };
    };

    it('Gets the first buffer', () => {
        const videoFrame = getVideoFrame(0);
        const result = getNextBuffer(videoFrame, [], ANNOTATOR_MODE.ACTIVE_LEARNING, FRAMESKIP, null);

        const startFrame = 0;
        expect(result).toEqual(getBuffer({ startFrame }));
    });

    it('gets the first buffer after the current frame', () => {
        const videoFrame = getVideoFrame(300);
        const result = getNextBuffer(videoFrame, [], ANNOTATOR_MODE.ACTIVE_LEARNING, FRAMESKIP, null);

        const startFrame = 240;
        expect(result).toEqual(getBuffer({ startFrame }));
    });

    it('gets the first buffer after the current frame ignoring previous buffers', () => {
        const videoFrame = getVideoFrame(300);
        const result = getNextBuffer(
            videoFrame,
            [getBuffer({ startFrame: 0, status: BufferStatus.SUCCESS })],
            ANNOTATOR_MODE.ACTIVE_LEARNING,
            FRAMESKIP,
            null
        );

        const startFrame = 240;
        expect(result).toEqual(getBuffer({ startFrame }));
    });

    it('returns any loading buffer', () => {
        const videoFrame = getVideoFrame(300);
        const result = getNextBuffer(
            videoFrame,
            [getBuffer({ startFrame: 0 })],
            ANNOTATOR_MODE.ACTIVE_LEARNING,
            FRAMESKIP,
            null
        );

        const startFrame = 0;
        expect(result).toEqual(getBuffer({ startFrame }));
    });

    it('returns the next buffer after the current buffer', () => {
        const videoFrame = getVideoFrame(300);
        const result = getNextBuffer(
            videoFrame,
            [
                getBuffer({ startFrame: 0, status: BufferStatus.SUCCESS }),
                getBuffer({ startFrame: 240, status: BufferStatus.SUCCESS }),
            ],
            ANNOTATOR_MODE.ACTIVE_LEARNING,
            FRAMESKIP,
            null
        );

        const startFrame = 480;
        expect(result).toEqual(getBuffer({ startFrame }));
    });

    it('returns the next buffer after the current buffer, while leaving a gap', () => {
        const videoFrame = getVideoFrame(500);
        const result = getNextBuffer(
            videoFrame,
            [
                getBuffer({ startFrame: 0, status: BufferStatus.SUCCESS }),
                getBuffer({ startFrame: 480, status: BufferStatus.SUCCESS }),
            ],
            ANNOTATOR_MODE.ACTIVE_LEARNING,
            FRAMESKIP,
            null
        );

        const startFrame = 720;
        expect(result).toEqual(getBuffer({ startFrame }));
    });

    it('caps the endFrame so that it does not grow past the video frames', () => {
        const videoFrame = getVideoFrame(5900);
        const result = getNextBuffer(videoFrame, [], ANNOTATOR_MODE.ACTIVE_LEARNING, FRAMESKIP, null);

        const startFrame = 5760;
        const endFrame = 5999;
        expect(result).toEqual(getBuffer({ startFrame, endFrame }));
    });

    it('does not go past the total frames of the video', () => {
        const videoFrame = getVideoFrame(5900);
        const startFrame = 5760;
        const endFrame = 5999;
        const result = getNextBuffer(
            videoFrame,
            [getBuffer({ startFrame, endFrame, status: BufferStatus.SUCCESS })],
            ANNOTATOR_MODE.ACTIVE_LEARNING,
            FRAMESKIP,
            null
        );

        expect(result).toEqual(undefined);
    });

    it('Stops buffering if it already finished loading the next 5 buffers', () => {
        const videoFrame = getVideoFrame(500);
        const result = getNextBuffer(
            videoFrame,
            [
                getBuffer({ startFrame: 480, status: BufferStatus.SUCCESS }),
                getBuffer({ startFrame: 720, status: BufferStatus.SUCCESS }),
                getBuffer({ startFrame: 960, status: BufferStatus.SUCCESS }),
                getBuffer({ startFrame: 1200, status: BufferStatus.SUCCESS }),
                getBuffer({ startFrame: 1440, status: BufferStatus.SUCCESS }),
            ],
            ANNOTATOR_MODE.ACTIVE_LEARNING,
            FRAMESKIP,
            null
        );

        expect(result).toBeUndefined();
    });
});

describe('isFrameInLoadedBuffer', () => {
    const index = 1;
    const bufferHandler = isFrameInLoadedBuffer(index);

    it('loading status', () => {
        expect(bufferHandler({ status: BufferStatus.LOADING, startFrame: index - 1, endFrame: index + 1 })).toBe(false);
    });

    it('success status', () => {
        expect(bufferHandler({ status: BufferStatus.SUCCESS, startFrame: index, endFrame: index })).toBe(true);
        expect(bufferHandler({ status: BufferStatus.SUCCESS, startFrame: index - 1, endFrame: index + 1 })).toBe(true);
    });

    it('out of range', () => {
        expect(bufferHandler({ status: BufferStatus.SUCCESS, startFrame: index + 1, endFrame: index + 2 })).toBe(false);
    });
});
