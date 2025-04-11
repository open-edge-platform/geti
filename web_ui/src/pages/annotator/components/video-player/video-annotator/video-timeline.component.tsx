// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { memo, MutableRefObject, useEffect, useMemo, useRef } from 'react';

import { Flex } from '@adobe/react-spectrum';
import useVirtual from 'react-cool-virtual';

import { Label } from '../../../../../core/labels/label.interface';
import { AdvancedFilterOptions } from '../../../../../core/media/media-filter.interface';
import { useFilterSearchParam } from '../../../../../hooks/use-filter-search-param/use-filter-search-param.hook';
import { useSize } from '../../../../../hooks/use-size/use-size.hook';
import { useMediaFilterEmpty } from '../../../hooks/use-media-filter-empty.hook';
import { useDataset } from '../../../providers/dataset-provider/dataset-provider.component';
import { useFilteredVideoFramesQuery } from '../hooks/use-filtered-video-frames-query.hook';
import { useActiveVideoFramesQuery } from '../hooks/useActiveVideoFramesQuery.hook';
import { getMaxVideoSliderValue } from '../utils';
import { useVideoPlayer } from '../video-player-provider.component';
import { VideoPlayerSlider } from '../video-player-slider/video-player-slider.component';
import { VideoFrameSegment } from './video-frame-segment.component';

import classes from './video-annotator.module.scss';

const MIN_SIZE_OF_SEGMENT = 2 * 8;

interface VideoTimelineProps {
    selectFrame: (frameNumber: number) => void;
    labels: readonly Label[];
}

const MemoVideoFrameSegment = memo(VideoFrameSegment);
const FRAMES_BEFORE_NEXT_TICK = 6;

export const VideoTimeline = ({ selectFrame, labels }: VideoTimelineProps): JSX.Element => {
    const ref = useRef<HTMLDivElement>(null);
    const size = useSize(ref);

    const { videoFrame, step, videoControls } = useVideoPlayer();
    const { isInActiveMode } = useDataset();

    const [mediaFilterOptions] = useFilterSearchParam<AdvancedFilterOptions>('filter', isInActiveMode);
    const isMediaFilterEmpty = useMediaFilterEmpty(mediaFilterOptions);

    const { data: activeVideoFrames } = useActiveVideoFramesQuery(videoFrame);
    const activeVideoFramesSet = useMemo(() => new Set(activeVideoFrames), [activeVideoFrames]);

    const { data: filteredFrames } = useFilteredVideoFramesQuery(videoFrame);
    const filteredFramesSet = useMemo(() => new Set<number>(filteredFrames as number[]), [filteredFrames]);

    const totalSegments = Math.max(Math.ceil(videoFrame.metadata.frames / step), 0);
    const sizePerSquare = size === undefined ? 0 : Math.max(MIN_SIZE_OF_SEGMENT, size.width / totalSegments);
    const frameOffset = Math.round(sizePerSquare / 2);

    const { outerRef, innerRef, items, scrollToItem } = useVirtual<HTMLDivElement, HTMLDivElement>({
        horizontal: true,
        itemCount: totalSegments,
        itemSize: sizePerSquare,
        overscanCount: 5,
    });

    useEffect(() => {
        const selectedVideoFrameIndex = Math.round(videoFrame.identifier.frameNumber / step);

        scrollToItem({ index: selectedVideoFrameIndex, align: 'center' });
    }, [videoFrame.identifier.frameNumber, step, scrollToItem]);

    const maxValue = getMaxVideoSliderValue(videoFrame.metadata.frames);

    return (
        <div
            ref={ref}
            className={classes.timeline}
            style={{ gridTemplateColumns: `repeat(auto-fit, minmax(${MIN_SIZE_OF_SEGMENT}px, max-content))` }}
        >
            <div ref={outerRef} className={classes.timelineOuterRef} style={{ width: size?.width }}>
                <div style={{ width: sizePerSquare * totalSegments }} className={classes.timelineSliderWrapper}>
                    <VideoPlayerSlider
                        frameOffset={frameOffset}
                        ref={outerRef as MutableRefObject<null>}
                        isInActiveMode={false}
                        mediaItem={videoFrame}
                        selectFrame={selectFrame}
                        step={step}
                        minValue={0}
                        maxValue={maxValue}
                        sizePerSquare={sizePerSquare}
                    />
                </div>
                <div
                    ref={innerRef}
                    className={classes.timelineInnerRef}
                    style={{ gridTemplateColumns: `repeat(auto-fit, minmax(${MIN_SIZE_OF_SEGMENT}px, max-content))` }}
                    role='grid'
                    aria-label={'Video timeline'}
                    aria-colcount={totalSegments}
                    aria-rowcount={labels.length}
                >
                    {items.map(({ index, size: width }) => {
                        const frameNumber = index * step;

                        const lastFrame = totalSegments - 1;
                        const isLastFrame = index === lastFrame;
                        const isFirstFrame = index === 0;
                        const isHalfFrame =
                            index + FRAMES_BEFORE_NEXT_TICK < lastFrame &&
                            index % Math.ceil((0.5 * (size?.width ?? 0)) / width) === 0;

                        const isActiveFrameMode = isInActiveMode && activeVideoFramesSet.has(frameNumber);

                        const isFilteredFrame =
                            !isInActiveMode && !isMediaFilterEmpty && filteredFramesSet.has(frameNumber);

                        const isSelectedFrame =
                            videoControls.isPlaying === false && videoFrame.identifier.frameNumber === frameNumber;

                        // Always show ticks at the start and end of the video or at every frame
                        // that is on half of the timeline
                        const showTicks = isFirstFrame || isHalfFrame || isLastFrame;

                        return (
                            <Flex justifyContent='center' alignItems='center' width={width} key={frameNumber}>
                                <MemoVideoFrameSegment
                                    colIndex={index}
                                    onClick={selectFrame}
                                    labels={labels}
                                    showTicks={showTicks}
                                    frameNumber={frameNumber}
                                    isSelectedFrame={isSelectedFrame}
                                    isActiveFrame={isActiveFrameMode}
                                    isFilteredFrame={isFilteredFrame}
                                    isLastFrame={isLastFrame}
                                    isFirstFrame={isFirstFrame}
                                />
                            </Flex>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};
