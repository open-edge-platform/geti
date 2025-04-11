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

import { RefObject, useState } from 'react';

import { Flex, View } from '@adobe/react-spectrum';
import { useSpinDelay } from 'spin-delay';

import { VideoFrame } from '../../../../core/media/video.interface';
import { Loading } from '../../../../shared/components/loading/loading.component';
import { useRequestVideoFrameCallback } from '../../hooks/use-request-video-frame-callback.hook';
import { Video } from '../video-player/video.component';
import { TransformZoom } from './transform-zoom.component';

interface VideoContentProps {
    mediaItem: VideoFrame;
    video: RefObject<HTMLVideoElement>;
    setFrameNumber: (number: number) => void;
    onPlay: () => void;
    onPause: () => void;
}

export const VideoContent = ({ mediaItem, video, setFrameNumber, onPlay, onPause }: VideoContentProps) => {
    const fps = mediaItem.metadata.fps;
    const [isVideoFrameLoading, setIsVideoFrameLoading] = useState<boolean>(false);

    const showLoading = useSpinDelay(isVideoFrameLoading, { delay: 100 });

    useRequestVideoFrameCallback(video, fps, (frameNumber) =>
        setFrameNumber(Math.min(frameNumber, mediaItem.metadata.frames - 1))
    );

    return (
        <Flex flex={1} marginBottom='size-100' minHeight='size-5000'>
            <View backgroundColor='gray-50' width='100%'>
                <TransformZoom mediaItem={mediaItem}>
                    <View position={'relative'}>
                        <Video
                            videoRef={video}
                            videoFrame={mediaItem}
                            onPlay={onPlay}
                            onPause={onPause}
                            onLoadStart={() => setIsVideoFrameLoading(true)}
                            onLoadedData={() => setIsVideoFrameLoading(false)}
                            onWaiting={() => setIsVideoFrameLoading(true)}
                            onSeeking={() => setIsVideoFrameLoading(true)}
                            onSeeked={() => setIsVideoFrameLoading(false)}
                            preload={'auto'}
                        />
                        {showLoading && <Loading overlay />}
                    </View>
                </TransformZoom>
            </View>
        </Flex>
    );
};
