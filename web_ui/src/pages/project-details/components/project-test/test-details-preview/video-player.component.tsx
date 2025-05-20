// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { ButtonGroup, Flex, View } from '@geti/ui';
import { StepBackward, StepForward } from '@geti/ui/icons';

import { MediaItem } from '../../../../../core/media/media.interface';
import { isVideoFrame, VideoFrame } from '../../../../../core/media/video.interface';
import { TestMediaItem } from '../../../../../core/tests/test-media.interface';
import { usePrevious } from '../../../../../hooks/use-previous/use-previous.hook';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { useConstructVideoFrame } from '../../../../annotator/components/video-player/hooks/use-construct-video-frame.hook';
import { VideoPlayerSlider } from '../../../../annotator/components/video-player/video-player-slider/video-player-slider.component';
import { useVideoControls } from './video-controls.hook';

export function VideoPlayer({
    testMediaItem,
    selectedMediaItem,
    setSelectedMediaItem,
}: {
    testMediaItem: TestMediaItem;
    selectedMediaItem: MediaItem;
    setSelectedMediaItem: (mediaItem: MediaItem) => void;
}) {
    const construct = useConstructVideoFrame(testMediaItem.media);
    const previousTestMediaItem = usePrevious(testMediaItem);

    useEffect(() => {
        if (testMediaItem === previousTestMediaItem || testMediaItem.type !== 'video') {
            return;
        }

        if (
            isVideoFrame(selectedMediaItem) &&
            selectedMediaItem.identifier.videoId === testMediaItem.media.identifier.videoId
        ) {
            return;
        }

        // If the selected media item doesn't belong to the test media item, then select
        // the first video frame from the test results
        const firstVideoFrame = construct(testMediaItem.filteredFrames[0].frameIndex);

        if (firstVideoFrame) {
            setSelectedMediaItem(firstVideoFrame);
        }
    }, [testMediaItem, previousTestMediaItem, construct, setSelectedMediaItem, selectedMediaItem]);

    const videoControls = useVideoControls({ testMediaItem, setSelectedMediaItem, selectedMediaItem });

    if (testMediaItem.type !== 'video' || videoControls === undefined) {
        return <></>;
    }

    return (
        <View
            borderWidth={'thin'}
            borderColor={'gray-50'}
            padding='size-100'
            paddingX='size-200'
            backgroundColor='gray-100'
        >
            <Flex width='100%' gap='size-100' alignContent={'center'} alignItems='center'>
                <ButtonGroup aria-label='Video controls'>
                    <QuietActionButton
                        onPress={videoControls.previous}
                        aria-label='Go to previous frame'
                        isDisabled={!videoControls.canSelectPrevious}
                        id='video-player-go-to-previous-frame'
                    >
                        <StepBackward />
                    </QuietActionButton>
                    <QuietActionButton
                        onPress={videoControls.next}
                        aria-label='Go to next frame'
                        isDisabled={!videoControls.canSelectNext}
                        id='video-player-go-to-next-frame'
                    >
                        <StepForward />
                    </QuietActionButton>
                </ButtonGroup>

                <View flexGrow={1}>
                    <VideoPlayerSlider
                        restrictedVideoFrames={testMediaItem.filteredFrames.map(({ frameIndex }) => frameIndex)}
                        isInActiveMode={false}
                        mediaItem={selectedMediaItem as VideoFrame}
                        selectFrame={videoControls.goto}
                        step={1}
                        minValue={0}
                        maxValue={testMediaItem.media.metadata.frames}
                    />
                </View>
            </Flex>
        </View>
    );
}
