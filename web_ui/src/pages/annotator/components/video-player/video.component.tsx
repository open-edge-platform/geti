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

import { CSSProperties, DetailedHTMLProps, RefObject, VideoHTMLAttributes } from 'react';

import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { VideoFrame } from '../../../../core/media/video.interface';
import { useApplicationServices } from '../../../../core/services/application-services-provider.component';
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
