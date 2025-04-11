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

import { MutableRefObject, useEffect, useLayoutEffect, useRef } from 'react';

export const useRequestVideoFrameCallback = (
    video: MutableRefObject<HTMLVideoElement | null | undefined>,
    fps: number,
    callback: (frameNumber: number) => void
) => {
    const animationFrameId = useRef<number>();

    const savedCallback = useRef(callback);

    useLayoutEffect(() => {
        savedCallback.current = callback;
    }, [callback]);

    useEffect(() => {
        if (!video.current) {
            return;
        }

        let requestFrame = requestAnimationFrame;
        let cancelFrame = cancelAnimationFrame;

        if (HTMLVideoElement.prototype !== undefined && 'requestVideoFrameCallback' in HTMLVideoElement.prototype) {
            // https://web.dev/requestvideoframecallback-rvfc/
            const vid = video.current as HTMLVideoElement & {
                requestVideoFrameCallback: typeof requestAnimationFrame;
                cancelVideoFrameCallback: typeof cancelAnimationFrame;
            };

            requestFrame = vid.requestVideoFrameCallback.bind(vid);
            cancelFrame = vid.cancelVideoFrameCallback.bind(vid);
        }

        const updateCanvas = (_time: number, metadata?: { mediaTime: number }) => {
            // To be honest I don't know if we really need to use metadata.mediaTime here
            const time = video.current?.currentTime ?? metadata?.mediaTime ?? 0;
            const frameNumber = Math.ceil(fps * time);

            savedCallback.current(frameNumber);
            animationFrameId.current = requestFrame(updateCanvas);
        };

        animationFrameId.current = requestFrame(updateCanvas);

        return () => {
            if (animationFrameId.current) {
                cancelFrame(animationFrameId.current);
            }
        };
    }, [video, fps]);
};
