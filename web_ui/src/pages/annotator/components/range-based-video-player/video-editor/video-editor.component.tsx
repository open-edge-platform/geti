// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useMemo, useState } from 'react';

import { Grid, View } from '@adobe/react-spectrum';
import groupBy from 'lodash/groupBy';

import { LabeledVideoRange } from '../../../../../core/annotations/labeled-video-range.interface';
import { recursivelyAddLabel, recursivelyRemoveLabels } from '../../../../../core/labels/label-resolver';
import { Label } from '../../../../../core/labels/label.interface';
import { VideoFrame } from '../../../../../core/media/video.interface';
import { VideoControls } from '../../../../../pages/annotator/components/video-player/video-controls/video-controls.interface';
import { hasEqualId } from '../../../../../shared/utils';
import { RangesList } from './ranges-list.component';
import { createNewRange } from './utils';
import { VideoNavigation } from './video-navigation.component';
import { VideoTimelineSlider } from './video-timeline-slider.component';

import classes from './video-player.module.scss';

interface VideoEditorProps {
    videoFrame: VideoFrame;
    videoControls: VideoControls;
    labels: Label[];
    ranges: LabeledVideoRange[];
    setRanges: (ranges: LabeledVideoRange[]) => void;
    isAnomaly: boolean;
}

const resolveLabelsForRange = (labels: Label[]) => {
    return (label: Label, rangeLabels: Label[]) => {
        return recursivelyAddLabel(
            rangeLabels as ReadonlyArray<Label>,
            label,
            labels as ReadonlyArray<Label>
        ) as Label[];
    };
};

export const VideoEditor = ({ videoFrame, videoControls, ranges, setRanges, labels, isAnomaly }: VideoEditorProps) => {
    const [sliderValue, setSliderValue] = useState(videoFrame.identifier.frameNumber);
    const [newRange, setNewRange] = useState<null | [number, number]>(null);
    const [isRangeSelectionEnabled, setIsRangeSelectionEnabled] = useState<boolean>(true);
    const frames = videoFrame.metadata.frames;

    const groupedLabels = useMemo(() => {
        return groupBy(labels, (label) => label.group);
    }, [labels]);

    const decoratedVideoControls = useMemo<VideoControls>(() => {
        if (!isRangeSelectionEnabled || newRange === null) {
            return videoControls;
        }

        const [startRange, endRage] = newRange;
        const fps = videoFrame.metadata.fps;
        const currentFrame = videoFrame.identifier.frameNumber;
        const nextFrame = currentFrame + 1.0 * fps;
        const previousFrame = currentFrame - 1.0 * fps;

        return {
            ...videoControls,
            canSelectNext: !(currentFrame === endRage || nextFrame > endRage) && videoControls.canSelectNext,
            canSelectPrevious:
                !(currentFrame === startRange || previousFrame < startRange) && videoControls.canSelectPrevious,
            canPlay: currentFrame < endRage && videoControls.canPlay,
        };
    }, [videoControls, newRange, videoFrame, isRangeSelectionEnabled]);

    useEffect(() => {
        if (
            videoFrame.identifier.frameNumber !== 0 &&
            newRange !== null &&
            // We cannot be sure that videoFrame.identifier.frameNumber goes 1 by 1 like range values, there might be
            // +-1 mismatch.
            videoFrame.identifier.frameNumber >= newRange[1]
        ) {
            decoratedVideoControls.pause?.();
        }
    }, [videoFrame.identifier.frameNumber, newRange, decoratedVideoControls]);

    useEffect(() => {
        setSliderValue(videoFrame.identifier.frameNumber);
    }, [videoFrame.identifier.frameNumber]);

    const updateLabelForRange = (inputRange: LabeledVideoRange): void => {
        const newRanges: LabeledVideoRange[] = ranges.map((range) => {
            if (range.start === inputRange.start && range.end === inputRange.end) {
                const newLabels = recursivelyRemoveLabels(range.labels, inputRange.labels) as Label[];

                return {
                    ...range,
                    labels: newLabels,
                };
            }
            return range;
        });

        setRanges(newRanges);
    };

    const handleSelectLabelForRange = (label: Label, range?: LabeledVideoRange) => {
        if (range !== undefined) {
            const hasLabel = range.labels.some(hasEqualId(label.id));

            if (!isAnomaly && hasLabel) {
                updateLabelForRange(range);

                return;
            }

            setRanges(createNewRange(ranges, { ...range, labels: [label] }, resolveLabelsForRange(labels)));

            setNewRange(null);

            setSliderValue(range.end);
            setTimeout(() => {
                decoratedVideoControls.goto(range.end);
            }, 0);
            return;
        }

        if (newRange === null) {
            return;
        }

        const [startRange, endRange] = newRange;

        const newRanges = createNewRange(
            ranges,
            { start: startRange, end: endRange, labels: [label] },
            resolveLabelsForRange(labels)
        );

        setRanges(newRanges);

        setNewRange(null);

        // Note: We want sliderValue to update UI immediately and then update visible video frame (in the future might
        // be replaced with startTransition)
        setSliderValue(endRange);
        setTimeout(() => {
            decoratedVideoControls.goto(endRange);
        }, 0);
    };

    const handleSliderValueChange = (value: number) => {
        if (newRange === null) {
            setSliderValue(value);
            return;
        }

        const [startRange, endRange] = newRange;

        if (value >= startRange && value <= endRange) {
            setSliderValue(value);
        }
    };

    const handleSliderValueChangeEnd = (value: number) => {
        if (newRange === null) {
            decoratedVideoControls.goto(value);
            return;
        }

        const [startRange, endRange] = newRange;

        if (value >= startRange && value <= endRange) {
            decoratedVideoControls.goto(value);
        } else if (value < startRange) {
            decoratedVideoControls.goto(startRange);
        } else if (value > endRange) {
            decoratedVideoControls.goto(endRange);
        }
    };

    const handleToggleRangeSelection = (value: boolean) => {
        setIsRangeSelectionEnabled(value);
        setNewRange(null);
    };

    return (
        <View paddingX='size-200' minHeight={0}>
            <Grid
                areas={['. controls', 'timeline timeline']}
                columns={['size-2000', 'auto']}
                rows={['size-500', 'auto', 'auto']}
                height={'100%'}
            >
                <VideoNavigation
                    videoFrame={videoFrame}
                    videoControls={decoratedVideoControls}
                    isRangeSelectionEnabled={isRangeSelectionEnabled}
                    onToggleRangeSelection={handleToggleRangeSelection}
                />

                <Grid
                    columns={['size-2000', '1fr']}
                    gridArea='timeline'
                    position={'relative'}
                    UNSAFE_className={classes.timelineWrapper}
                >
                    <View width='100%' position={'absolute'} gridColumn={'2 / 3'}>
                        <VideoTimelineSlider
                            sliderValue={sliderValue}
                            onSliderValueChange={handleSliderValueChange}
                            videoFrame={videoFrame}
                            onSliderValueChangeEnd={handleSliderValueChangeEnd}
                        />
                    </View>

                    <RangesList
                        groupedLabels={groupedLabels}
                        setNewRange={setNewRange}
                        sliderValue={sliderValue}
                        ranges={ranges}
                        isRangeSelectionEnabled={isRangeSelectionEnabled}
                        newRange={newRange}
                        onSelectLabelForRange={handleSelectLabelForRange}
                        maxFrame={frames - 1}
                    />
                </Grid>
            </Grid>
        </View>
    );
};
