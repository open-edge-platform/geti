// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RefObject, useState } from 'react';

import { Flex, Loading, View } from '@geti/ui';
import { useSpinDelay } from 'spin-delay';

import { VideoFrame } from '../../../../core/media/video.interface';
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
                        {showLoading && <Loading mode='overlay' />}
                    </View>
                </TransformZoom>
            </View>
        </Flex>
    );
};
