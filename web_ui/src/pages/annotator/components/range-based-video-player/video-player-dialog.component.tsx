// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useRef, useState } from 'react';

import { ButtonGroup, Content, Dialog, Divider, Flex, Heading, View } from '@adobe/react-spectrum';

import { LabeledVideoRange } from '../../../../core/annotations/labeled-video-range.interface';
import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { Video, VideoFrame } from '../../../../core/media/video.interface';
import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import { isAnomalyDomain } from '../../../../core/projects/domains';
import { VideoControls } from '../../../../pages/annotator/components/video-player/video-controls/video-controls.interface';
import { ZoomProvider } from '../../../../pages/annotator/zoom/zoom-provider.component';
import { Button } from '../../../../shared/components/button/button.component';
import { LoadingIndicator } from '../../../../shared/components/loading/loading-indicator.component';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import UndoRedoProvider from '../../tools/undo-redo/undo-redo-provider.component';
import useUndoRedoState from '../../tools/undo-redo/use-undo-redo-state';
import { Footer } from '../footer/annotator-footer.component';
import { useLabeledVideoRangesMutation, useLabeledVideoRangesQuery } from './use-labeled-video-ranges.hook';
import { VideoContent } from './video-content.component';
import { fillRangesWithEmptyRanges } from './video-editor/utils';
import { VideoEditor } from './video-editor/video-editor.component';

const useVideoPlayerVideoControls = (mediaItem: Video) => {
    const video = useRef<HTMLVideoElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [frameNumber, setFrameNumber] = useState(0);

    const fps = mediaItem.metadata.fps;

    const videoFrame: VideoFrame = {
        ...mediaItem,
        identifier: { ...mediaItem.identifier, type: MEDIA_TYPE.VIDEO_FRAME, frameNumber },
    };
    const videoControls: VideoControls = {
        canSelectNext: frameNumber < mediaItem.metadata.frames - 1,
        canSelectPrevious: frameNumber > 0,
        canPlay: true,
        isPlaying,
        goto: (newFrameNumber: number) => {
            if (video.current) {
                video.current.currentTime = newFrameNumber / fps;
            }
        },
        next: () => {
            if (video.current) {
                video.current.currentTime += 1.0;
            }
        },
        previous: () => {
            if (video.current) {
                video.current.currentTime -= 1.0;
            }
        },
        pause: () => {
            if (video.current) {
                setIsPlaying(false);
                video.current.pause();
            }
        },
        play: () => {
            if (video.current) {
                setIsPlaying(true);
                video.current.play();
            }
        },
    };

    return {
        video,
        isPlaying,
        setIsPlaying,
        videoControls,
        videoFrame,
        setFrameNumber,
    };
};

export const VideoPlayerDialog = ({
    datasetIdentifier,
    mediaItem,
    close,
}: {
    datasetIdentifier: DatasetIdentifier;
    mediaItem: Video;
    close: () => void;
}) => {
    const { video, setIsPlaying, videoControls, videoFrame, setFrameNumber } = useVideoPlayerVideoControls(mediaItem);
    const [ranges, setRanges, undoRedoState] = useUndoRedoState<LabeledVideoRange[]>([
        { start: 0, end: videoFrame.metadata.frames - 1, labels: [] },
    ]);

    const {
        project: { labels },
        isSingleDomainProject,
    } = useProject();

    const resetRanges = (inputRanges: LabeledVideoRange[]) => {
        const lastRange = inputRanges.at(-1);
        let finalInputRanges = inputRanges;

        // Remove it when backend fixes issue with end_frame. The issue is when user annotates video while uploading
        // media item. It causes end_frame to be equal to the number of frames in the video.
        if (lastRange !== undefined && lastRange.end > videoFrame.metadata.frames - 1) {
            finalInputRanges = [...inputRanges.slice(0, -1), { ...lastRange, end: videoFrame.metadata.frames - 1 }];
        }

        const newRanges = fillRangesWithEmptyRanges(finalInputRanges, videoFrame.metadata.frames - 1);
        undoRedoState.reset(newRanges);
    };

    const rangesQuery = useLabeledVideoRangesQuery(datasetIdentifier, mediaItem, labels, resetRanges);
    const rangesMutation = useLabeledVideoRangesMutation(datasetIdentifier, mediaItem);

    const handleSaveSelection = () => {
        rangesMutation.mutate(ranges, { onSuccess: close });
    };

    return (
        <Dialog width='90vw' height='90vh' maxHeight={'unset'}>
            <Heading>Quick annotation - label ranges</Heading>

            <Divider />

            {rangesQuery.isFetching ? (
                <Content UNSAFE_style={{ overflowY: 'visible' }} height='size-4600'>
                    <LoadingIndicator />
                </Content>
            ) : (
                <Content UNSAFE_style={{ overflowY: 'visible' }}>
                    <ZoomProvider>
                        <View borderWidth='thin' borderColor='gray-50' borderRadius='medium' height='100%'>
                            <Flex direction='column' height='100%'>
                                <VideoContent
                                    mediaItem={videoFrame}
                                    video={video}
                                    onPause={() => setIsPlaying(false)}
                                    onPlay={() => setIsPlaying(true)}
                                    setFrameNumber={setFrameNumber}
                                />

                                <UndoRedoProvider state={undoRedoState}>
                                    <VideoEditor
                                        labels={labels}
                                        ranges={ranges}
                                        setRanges={setRanges}
                                        videoFrame={videoFrame}
                                        videoControls={videoControls}
                                        isAnomaly={isSingleDomainProject(isAnomalyDomain)}
                                    />
                                </UndoRedoProvider>

                                <Footer selectedItem={videoFrame} />
                            </Flex>
                        </View>
                    </ZoomProvider>
                </Content>
            )}

            <ButtonGroup isDisabled={rangesQuery.isFetching || rangesMutation.isPending}>
                <Button variant='secondary' onPress={close}>
                    Cancel
                </Button>
                <Button variant='accent' onPress={handleSaveSelection} isDisabled={!undoRedoState.canUndo}>
                    {rangesMutation.isPending ? <LoadingIndicator size='S' marginEnd='size-100' /> : <></>}
                    Save ranges
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};
