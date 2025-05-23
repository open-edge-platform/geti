// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, DetailedHTMLProps, RefObject, VideoHTMLAttributes } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';

import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { VideoFrame } from '../../../../core/media/video.interface';
import { useDatasetIdentifier } from '../../hooks/use-dataset-identifier.hook';

const useVideoSrc = (videoFrame: VideoFrame) => {
    const datasetIdentifier = useDatasetIdentifier();
    const { router } = useApplicationServices();

    return router.MEDIA_ITEM_STREAM(datasetIdentifier, {
        ...videoFrame.identifier,
        type: MEDIA_TYPE.VIDEO,
    });
};

interface VideoProps extends DetailedHTMLProps<VideoHTMLAttributes<HTMLVideoElement>, HTMLVideoElement> {
    videoRef: RefObject<HTMLVideoElement>;
    videoFrame: VideoFrame;
    onPlay: () => void;
    onPause: () => void;
    onLoad?: () => void;
    style?: CSSProperties;
}

export const Video = ({ videoRef, videoFrame, onLoad, onPlay, onPause, ...props }: VideoProps) => {
    const src = useVideoSrc(videoFrame);

    return (
        <video
            src={src}
            ref={videoRef}
            width={videoFrame.metadata.width}
            onLoad={onLoad}
            onLoadedData={onLoad}
            onPlay={onPlay}
            onPause={onPause}
            crossOrigin='use-credentials'
            controlsList='noremoteplayback'
            style={{ outline: 'none', ...props.style }}
            muted
            {...props}
        />
    );
};
