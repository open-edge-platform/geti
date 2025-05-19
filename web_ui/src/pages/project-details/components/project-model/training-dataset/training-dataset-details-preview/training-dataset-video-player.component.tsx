// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useEffect, useMemo } from 'react';

import { Flex, View } from '@adobe/react-spectrum';
import { Loading } from '@geti/ui';
import { sortBy } from 'lodash-es';

import { useTrainingDatasetVideo } from '../../../../../../core/datasets/hooks/use-training-dataset.hook';
import {
    AdvancedFilterOptions,
    AdvancedFilterSortingOptions,
} from '../../../../../../core/media/media-filter.interface';
import { Video, VideoFrame } from '../../../../../../core/media/video.interface';
import { useProjectIdentifier } from '../../../../../../hooks/use-project-identifier/use-project-identifier';
import { useConstructVideoFrame } from '../../../../../annotator/components/video-player/hooks/use-construct-video-frame.hook';
import { VideoPlayerSlider } from '../../../../../annotator/components/video-player/video-player-slider/video-player-slider.component';
import { TrainingDatasetVideoControls } from './training-dataset-video-controls.component';

export function TrainingDatasetVideoPlayer({
    videoItem,
    selectedFrame,
    setSelectedFrame,
    storageId,
    revisionId,
    searchOptions,
    sortingOptions,
}: {
    videoItem: Video;
    selectedFrame: VideoFrame;
    setSelectedFrame: (mediaItem: VideoFrame) => void;
    storageId: string;
    revisionId: string;
    sortingOptions: AdvancedFilterSortingOptions;
    searchOptions: AdvancedFilterOptions;
}) {
    const projectIdentifier = useProjectIdentifier();
    const construct = useConstructVideoFrame(videoItem);

    const { data, isSuccess } = useTrainingDatasetVideo(
        projectIdentifier,
        storageId,
        revisionId,
        videoItem.identifier.videoId,
        searchOptions,
        sortingOptions
    );

    const framesIndices = useMemo(() => {
        return (
            sortBy(
                data?.frames.map(({ identifier }) => identifier.frameNumber),
                (number) => number
            ) || []
        );
    }, [data]);

    const orderedFrames = useMemo(() => sortBy(data?.frames, ({ identifier }) => identifier.frameNumber), [data]);

    const goto = useCallback(
        (frameNumber: number) => {
            const videoFrame = construct(frameNumber, orderedFrames);

            if (videoFrame) {
                setSelectedFrame(videoFrame);
            }
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [setSelectedFrame, orderedFrames]
    );

    useEffect(() => {
        isSuccess && goto(framesIndices[0]);
    }, [isSuccess, framesIndices, goto]);

    if (selectedFrame && isSuccess) {
        return (
            <View
                borderYWidth={'thin'}
                borderColor={'gray-50'}
                padding='size-100'
                paddingX='size-200'
                backgroundColor='gray-100'
            >
                <Flex width='100%' gap='size-100' alignContent={'center'} alignItems='center'>
                    <TrainingDatasetVideoControls
                        frameNumber={selectedFrame.identifier.frameNumber}
                        frames={framesIndices}
                        selectFrame={goto}
                    />

                    <View flexGrow={1}>
                        <VideoPlayerSlider
                            restrictedVideoFrames={framesIndices}
                            isInActiveMode={false}
                            mediaItem={selectedFrame}
                            selectFrame={goto}
                            step={1}
                            minValue={0}
                            maxValue={videoItem.metadata.frames}
                        />
                    </View>
                </Flex>
            </View>
        );
    }

    return <Loading />;
}
