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

import { ReactNode, useState } from 'react';

import { View } from '@adobe/react-spectrum';
import { useSpinDelay } from 'spin-delay';

import { getAnnotationStateForTask } from '../../../core/annotations/utils';
import { isImage } from '../../../core/media/image.interface';
import { MediaItem } from '../../../core/media/media.interface';
import { isVideo, isVideoFrame } from '../../../core/media/video.interface';
import { AnnotationStateIndicator } from '../annotation-indicator/annotation-state-indicator.component';
import { VideoAnnotationIndicator } from '../annotation-indicator/video-annotation-indicator.component';
import { Skeleton } from '../skeleton/skeleton.component';
import { VideoFrameNumberIndicator } from '../video-indicator/video-frame-number-indicator.component';
import { VideoIndicator } from '../video-indicator/video-indicator.component';

import classes from '../../shared.module.scss';

interface MediaItemViewProps {
    mediaItem: MediaItem;
    itemMenu?: ReactNode;
    shouldShowAnnotationIndicator: boolean;
    shouldShowVideoIndicator?: boolean;
}

export const MediaItemView = ({
    itemMenu,
    mediaItem,
    shouldShowAnnotationIndicator,
    shouldShowVideoIndicator = true,
}: MediaItemViewProps): JSX.Element => {
    const [isImageLoaded, setImageLoaded] = useState<boolean>(false);
    const { name, thumbnailSrc, annotationStatePerTask } = mediaItem;
    const resolution = `(${mediaItem.metadata.width}x${mediaItem.metadata.height})`;

    const showLoadingSpinner = useSpinDelay(!isImageLoaded, { delay: 100 });

    return (
        <View
            position={'relative'}
            height={'100%'}
            width={'100%'}
            overflow={'hidden'}
            UNSAFE_className={classes.scaling}
        >
            {!showLoadingSpinner && itemMenu}

            {showLoadingSpinner && (
                <Skeleton isAspectRatioOne id={'image-placeholder-id'} data-testid={'image-placeholder-id'} />
            )}

            <img
                key={thumbnailSrc}
                width={'100%'}
                height={'100%'}
                alt={name}
                data-testid={`${name}${resolution}`}
                src={thumbnailSrc}
                onLoad={() => setImageLoaded(true)}
                style={{
                    display: showLoadingSpinner ? 'none' : 'block',
                }}
                // @ts-expect-error fetchPriority isn't recognized by react yet
                // eslint-disable-next-line react/no-unknown-property
                fetchpriority='low'
            />

            {shouldShowAnnotationIndicator && isImage(mediaItem) && (
                <AnnotationStateIndicator
                    state={getAnnotationStateForTask(annotationStatePerTask)}
                    id={mediaItem.name}
                />
            )}

            {shouldShowAnnotationIndicator && isVideo(mediaItem) && <VideoAnnotationIndicator video={mediaItem} />}

            {shouldShowVideoIndicator && isVideo(mediaItem) && (
                <VideoIndicator duration={mediaItem.metadata.duration} frames={mediaItem.matchedFrames} />
            )}

            {isVideoFrame(mediaItem) && shouldShowVideoIndicator && (
                <VideoFrameNumberIndicator frameNumber={mediaItem.identifier.frameNumber} />
            )}
        </View>
    );
};
