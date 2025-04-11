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

import { useState } from 'react';

import { Flex, Text, ToggleButton, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

import { ChevronDownLight, ChevronUpLight } from '../../../../assets/icons';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { useDataset } from '../../providers/dataset-provider/dataset-provider.component';
import { Duration } from '../footer/duration.component';
import { FrameStep } from './frame-step/frame-step.component';
import { useFilteredVideoFramesQuery } from './hooks/use-filtered-video-frames-query.hook';
import { useVideoControlsWithSaveConfirmation } from './hooks/use-video-controls-with-save-confirmation.hook';
import { PropagateAnnotations } from './propagate-annotations/propagate-annotations.component';
import { PlaybackSpeedSlider } from './streaming-video-player/playback-rate-slider.component';
import { useIsStreamingVideoPlayerEnabled } from './streaming-video-player/streaming-video-player-provider.component';
import { getMaxVideoSliderValue } from './utils';
import { VideoAnnotator } from './video-annotator/video-annotator.component';
import { StreamingVideoControls } from './video-controls/streaming-video-controls.component';
import { Controls } from './video-controls/video-controls.component';
import { VideoFrames } from './video-frames/video-frames.component';
import { useVideoPlayer } from './video-player-provider.component';
import { VideoPlayerSlider } from './video-player-slider/video-player-slider.component';

export const VideoPlayer = (): JSX.Element => {
    const [isExpanded, setIsExpanded] = useState(true);

    const { isInActiveMode } = useDataset();
    const { videoFrame, step, setStep } = useVideoPlayer();
    const videoControls = useVideoControlsWithSaveConfirmation();
    const { data: filteredFrames } = useFilteredVideoFramesQuery(videoFrame);
    const isStreamingVideoPlayerEnabled = useIsStreamingVideoPlayerEnabled(videoFrame);

    const maxValue = getMaxVideoSliderValue(videoFrame.metadata.frames);

    return (
        <View gridArea='videoplayer' padding='size-100' paddingX='size-200' backgroundColor='gray-100'>
            <Flex gap='size-200' direction='column'>
                <Flex gap='size-150' alignItems='center' height='100%'>
                    <Text>Frames</Text>
                    {isStreamingVideoPlayerEnabled ? (
                        <StreamingVideoControls videoControls={videoControls} />
                    ) : (
                        <Controls videoControls={videoControls} />
                    )}

                    <Duration isLargeSize={false} mediaItem={videoFrame} />

                    {isStreamingVideoPlayerEnabled && isExpanded && (
                        <>
                            <Divider orientation={'vertical'} size={'S'} />
                            <FrameStep
                                step={step}
                                setStep={setStep}
                                defaultFps={videoFrame.metadata.frameStride}
                                isDisabled={videoControls.isPlaying}
                            />
                            <PlaybackSpeedSlider />
                            <Divider orientation={'vertical'} size={'S'} />
                        </>
                    )}

                    {isExpanded ? (
                        <Flex gap='size-200' marginStart='auto' alignItems={'center'}>
                            <VideoFrames
                                currentFrameNumber={videoFrame.identifier.frameNumber}
                                totalFramesNumber={videoFrame.metadata.frames - 1}
                            />

                            <PropagateAnnotations />

                            <TooltipTrigger placement={'top'}>
                                <ToggleButton
                                    onPress={() => setIsExpanded(false)}
                                    isQuiet
                                    isSelected
                                    id={`videoplayer-fold-unfold-button`}
                                    aria-label='Close video annotator'
                                >
                                    <ChevronDownLight />
                                </ToggleButton>
                                <Tooltip>Collapse video annotator</Tooltip>
                            </TooltipTrigger>
                        </Flex>
                    ) : (
                        <>
                            <View flexGrow={1}>
                                <VideoPlayerSlider
                                    highlightedFrames={isInActiveMode ? [] : filteredFrames}
                                    isInActiveMode={isInActiveMode}
                                    mediaItem={videoFrame}
                                    selectFrame={videoControls.goto}
                                    step={step}
                                    minValue={0}
                                    maxValue={maxValue}
                                />
                            </View>

                            <TooltipTrigger placement={'top'}>
                                <ToggleButton
                                    onPress={() => setIsExpanded(true)}
                                    isQuiet
                                    isSelected={false}
                                    id={`videoplayer-fold-unfold-button`}
                                    aria-label='Open video annotator'
                                >
                                    <ChevronUpLight />
                                </ToggleButton>
                                <Tooltip>Open video annotator</Tooltip>
                            </TooltipTrigger>
                        </>
                    )}
                </Flex>
                {isExpanded ? <VideoAnnotator selectFrame={videoControls.goto} /> : <></>}
            </Flex>
        </View>
    );
};
