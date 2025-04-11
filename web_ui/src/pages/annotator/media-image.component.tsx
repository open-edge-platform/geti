// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { mediaIdentifierToString, MediaItem } from '../../core/media/media.interface';
import { useDrawImageOnCanvas } from '../../shared/hooks/use-draw-image-on-canvas.hook';
import { useIsStreamingVideoPlayerEnabled } from './components/video-player/streaming-video-player/streaming-video-player-provider.component';
import { VideoFrame } from './components/video-player/video-frame.component';

import classes from './annotator-canvas.module.scss';

interface MediaImageProps {
    image: ImageData;
    selectedMediaItem: MediaItem | undefined;
}

// Due to security / privacy reasons all images in Geti are served with the no-cache,
// no-store header. Thus whenever this component is remounted the browser will
// redownload the image.
// To avoid this we store the image in a react-query query and draw the image using
// a canvas element instead
export const MediaImage = ({ image, selectedMediaItem }: MediaImageProps): JSX.Element => {
    const enableVideoPlayerCanvas = useIsStreamingVideoPlayerEnabled(selectedMediaItem);
    const ref = useDrawImageOnCanvas({ image });

    return (
        <div id={'annotations-canvas-image'} data-testid={'annotations-canvas-image'} style={{ position: 'relative' }}>
            <canvas
                id={selectedMediaItem !== undefined ? mediaIdentifierToString(selectedMediaItem.identifier) : undefined}
                className={classes.image}
                ref={ref}
                width={image.width}
                height={image.height}
            />

            {enableVideoPlayerCanvas && (
                <VideoFrame
                    key={selectedMediaItem.identifier.videoId}
                    selectedMediaItem={selectedMediaItem}
                    canvasRef={ref}
                />
            )}
        </div>
    );
};
