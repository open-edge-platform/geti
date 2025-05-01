// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Image, View } from '@adobe/react-spectrum';
import { AnnotationStateIndicator } from '@shared/components/annotation-indicator/annotation-state-indicator.component';
import { FrameNumberIndicator } from '@shared/components/frame-number-indicator/frame-number-indicator.component';
import { useDurationText } from '@shared/hooks/data-format/use-duration-text.hook';

import { getAnnotationStateForTask } from '../../../../../core/annotations/utils';
import { VideoFrame } from '../../../../../core/media/video.interface';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { useConstructVideoFrame } from '../hooks/use-construct-video-frame.hook';

interface ThumbnailPreviewProps {
    videoFrame: number;
    mediaItem: VideoFrame;
    width: number;
    height: number;
    x: number;
}

export const ThumbnailPreview = ({
    mediaItem,
    videoFrame: frameNumber,
    width,
    height,
    x,
}: ThumbnailPreviewProps): JSX.Element => {
    const constructVideoFrame = useConstructVideoFrame(mediaItem);
    const videoFrame = constructVideoFrame(frameNumber) as VideoFrame;

    const fps = videoFrame.metadata.fps;
    const src = videoFrame.thumbnailSrc;

    const durationText = useDurationText(frameNumber / fps);
    const { selectedTask } = useTask();

    return (
        <View
            position='absolute'
            top={-height - 25}
            left={x - width / 2}
            overflow='hidden'
            borderRadius='small'
            UNSAFE_style={{ boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.38)', pointerEvents: 'none' }}
        >
            <View position='fixed'>
                <AnnotationStateIndicator
                    id={videoFrame.name}
                    state={getAnnotationStateForTask(videoFrame.annotationStatePerTask, selectedTask)}
                />
                <FrameNumberIndicator frameNumber={frameNumber} />
                <Image
                    src={src}
                    alt={`Thumbnail for frame ${frameNumber}`}
                    objectFit='cover'
                    height={height}
                    width={width}
                />
                <View
                    backgroundColor='gray-50'
                    paddingX='size-75'
                    paddingY='size-25'
                    alignSelf='center'
                    UNSAFE_style={{ color: 'white', fontSize: '11px', textAlign: 'center' }}
                >
                    {durationText}
                </View>
                <View backgroundColor='static-white' width='1px' marginX='auto' height='size-200'>
                    &nbsp;
                </View>
            </View>
        </View>
    );
};
