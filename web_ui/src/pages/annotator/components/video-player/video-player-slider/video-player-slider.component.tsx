// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ForwardedRef, forwardRef, PointerEvent, RefObject, useEffect, useRef, useState } from 'react';

import { DOMRefValue } from '@react-types/shared';
import isEmpty from 'lodash/isEmpty';
import minBy from 'lodash/minBy';
import { useHover } from 'react-aria';

import { VideoFrame } from '../../../../../core/media/video.interface';
import { useDebouncedCallback } from '../../../../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { blurActiveInput } from '../../../tools/utils';
import { FRAME_STEP_TO_DISPLAY_ALL_FRAMES } from '../../utils';
import { useStreamingVideoPlayerContext } from '../streaming-video-player/streaming-video-player-provider.component';
import { ThumbnailPreview } from './thumbnail-preview.component';
import { VideoSlider } from './video-slider.component';

import classes from './video-player-slider.module.scss';

const getFrameNumber = (x: number, width: number, minValue: number, maxValue: number, step: number) => {
    const frameNumber = Math.min(
        Math.floor(maxValue / step) * step,
        Math.max(0, Math.round(Math.round((x / width) * (maxValue - minValue)) / step) * step)
    );

    return frameNumber;
};

const DisabledSlider = () => {
    return (
        <div className={classes.sliderWrapper}>
            <VideoSlider
                isDisabled
                id='video-player-timeline-slider'
                width='100%'
                aria-label='Videoframe'
                showValueLabel={false}
                highlightedFrames={[]}
                buffers={[]}
                lastFrame={100}
            />
        </div>
    );
};

interface VideoPlayerSliderProps {
    restrictedVideoFrames?: number[];
    highlightedFrames?: number[];
    isInActiveMode: boolean;
    mediaItem: VideoFrame;
    selectFrame: (frameNumber: number) => void;
    step: number;
    maxValue: number;
    minValue: number;
    frameOffset?: number;
    sizePerSquare?: number;
}

const getContainerScroll = (ref: ForwardedRef<HTMLDivElement>) => {
    const containerRef = ref as RefObject<DOMRefValue<HTMLDivElement>>;

    if (containerRef?.current) {
        return (containerRef?.current as unknown as HTMLDivElement)?.scrollLeft ?? 0;
    }

    return 0;
};

const THUMBNAIL_DELAY = 1000;
export const VideoPlayerSlider = forwardRef<HTMLDivElement, VideoPlayerSliderProps>(
    (
        {
            mediaItem,
            selectFrame,
            step,
            isInActiveMode,
            restrictedVideoFrames,
            maxValue,
            minValue,
            highlightedFrames = [],
            frameOffset = 0,
            sizePerSquare,
        },
        ref
    ): JSX.Element => {
        const timeoutRef = useRef<ReturnType<typeof setTimeout>>();
        const [showThumbnail, setShowThumbnail] = useState(false);
        const [thumbnailPosition, setThumbnailPosition] = useState<null | number>(null);

        const [thumbnailVideoFrame, setThumbnailVideoFrame] = useState<null | number>(null);
        const setThumbnailVideoFrameDebounced = useDebouncedCallback(setThumbnailVideoFrame, 200);

        const frameNumber = mediaItem.identifier.frameNumber;
        const containerScrollLeft = getContainerScroll(ref);
        const buffers = useStreamingVideoPlayerContext()?.buffers ?? [];
        const [sliderValue, setSliderValue] = useState(frameNumber);

        const isDisplayingFrames = FRAME_STEP_TO_DISPLAY_ALL_FRAMES === step;
        const lastFrame = isDisplayingFrames ? mediaItem.metadata.frames : mediaItem.metadata.frames - step;

        const { hoverProps } = useHover({
            onHoverStart: () => {
                timeoutRef.current = setTimeout(() => setShowThumbnail(true), THUMBNAIL_DELAY);
            },
            onHoverEnd: () => {
                timeoutRef.current && clearTimeout(timeoutRef.current);
                setShowThumbnail(false);
                setThumbnailPosition(null);
                setThumbnailVideoFrameDebounced(null);
            },
        });

        useEffect(() => setSliderValue(frameNumber), [frameNumber]);

        useEffect(() => {
            return () => {
                timeoutRef.current && clearTimeout(timeoutRef.current);
            };
        }, []);

        // The videoFrames can be empty when the user uses active frames and the active
        // set for this video is empty.
        if (restrictedVideoFrames !== undefined && isEmpty(restrictedVideoFrames)) {
            return <DisabledSlider />;
        }

        const findNearestVideoFrame = (toFrameNumber: number): number => {
            // Get the nearest video frame
            const videoFrame =
                restrictedVideoFrames === undefined
                    ? toFrameNumber
                    : minBy(restrictedVideoFrames, (allowedFrameNumber) => {
                          return Math.abs(toFrameNumber - allowedFrameNumber);
                      });

            // minBy only returns undefined if videoFrames is empty, in this case we
            // default to the currently selected video frame
            if (videoFrame === undefined) {
                return mediaItem.identifier.frameNumber;
            }

            return videoFrame;
        };

        const onPointerMove = (event: PointerEvent<HTMLDivElement>): void => {
            const rect = event.currentTarget.getBoundingClientRect();
            const thumbnailPosX = Math.max(0, event.clientX - rect.x) - containerScrollLeft;

            const thumbnailFrameNumber = getFrameNumber(
                thumbnailPosX - frameOffset + containerScrollLeft,
                rect.width,
                minValue ?? 0,
                maxValue ?? 0,
                step
            );

            const videoFrame = findNearestVideoFrame(thumbnailFrameNumber);

            if (videoFrame !== undefined) {
                setThumbnailPosition(thumbnailPosX);
                setThumbnailVideoFrameDebounced(videoFrame);
            }
        };

        return (
            <div className={classes.sliderWrapper} onPointerMove={onPointerMove} {...hoverProps}>
                <VideoSlider
                    id='video-player-timeline-slider'
                    leftOffset={frameOffset}
                    sizePerSquare={sizePerSquare}
                    highlightedFrames={highlightedFrames}
                    onChangeEnd={(newFrameNumber) => {
                        const videoFrame = findNearestVideoFrame(newFrameNumber);

                        selectFrame(videoFrame);
                        blurActiveInput(true);
                    }}
                    value={sliderValue}
                    onChange={(newFrameNumber: number) => {
                        const videoFrame = findNearestVideoFrame(newFrameNumber);

                        setSliderValue(videoFrame);
                        setShowThumbnail(true);
                    }}
                    defaultValue={frameNumber}
                    minValue={minValue}
                    maxValue={maxValue}
                    step={isInActiveMode ? 1 : step}
                    aria-label='Videoframe'
                    showValueLabel={false}
                    isFilled
                    width='100%'
                    buffers={buffers}
                    lastFrame={lastFrame}
                />
                {showThumbnail && thumbnailVideoFrame !== null && thumbnailPosition !== null ? (
                    <ThumbnailPreview
                        x={thumbnailPosition}
                        width={100}
                        height={100}
                        videoFrame={thumbnailVideoFrame}
                        mediaItem={mediaItem}
                    />
                ) : (
                    <></>
                )}
            </div>
        );
    }
);
