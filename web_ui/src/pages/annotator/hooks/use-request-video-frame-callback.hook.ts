// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
