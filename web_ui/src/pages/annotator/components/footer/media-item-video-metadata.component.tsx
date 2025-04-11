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

import { useMediaQuery } from '@react-spectrum/utils';

import { isVideoFrame, Video, VideoFrame } from '../../../../core/media/video.interface';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { FPS } from './fps.component';
import { FrameNumber } from './frame-number.component';
import { LastAnnotator } from './last-annotator.component';
import { MediaNameAndResolution } from './media-name-and-resolution.component';

import classes from './annotator-footer.module.scss';

export const MediaItemVideoMetadata = ({ mediaItem }: { mediaItem: Video | VideoFrame }): JSX.Element => {
    const { width, height } = mediaItem.metadata;
    const isLargeSize = useMediaQuery(isLargeSizeQuery);

    return (
        <>
            {mediaItem.lastAnnotatorId && (
                <LastAnnotator isLargeSize={isLargeSize} lastAnnotatorId={mediaItem.lastAnnotatorId} />
            )}
            <MediaNameAndResolution isLargeSize={isLargeSize} width={width} height={height} name={mediaItem.name} />

            <FPS mediaItem={mediaItem} className={classes.metaItem} />
            {isVideoFrame(mediaItem) && <FrameNumber mediaItem={mediaItem} className={classes.frameNumber} />}
        </>
    );
};
