// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import type { Media, MediaVideo } from '@/api/types';
import { Flex } from '@geti-ui/ui';

import { useIsScrolling } from '../../hooks/use-is-scrolling.hook';
import { isVideo } from '../../shared/media-item-utils';
import { formatCompactDuration } from './util';

import classes from './media-thumbnail.module.scss';

type MediaThumbnailProps = {
    onClick?: () => void;
    onDoubleClick?: () => void;
    url: string;
    alt: string;
    item: Pick<Media, 'type'> | Pick<MediaVideo, 'type' | 'frame_count' | 'annotated_frame_count' | 'duration'>;
};

// Only request a thumbnail once scrolling stops: fast scrolling unmounts thumbnails mid-request,
// and enough cancelled requests wedge the HTTP/2 connection. Once set, src is never cleared.
const useSettledSrc = (url: string): string | undefined => {
    const isScrolling = useIsScrolling();
    const [src, setSrc] = useState<string>();

    if (src === undefined && !isScrolling) {
        setSrc(url);
    }

    return src;
};

type VideoIndicatorProps = {
    duration: number;
};

const VideoIndicator = ({ duration }: VideoIndicatorProps) => {
    return (
        <Flex
            gap={'size-50'}
            left={'size-50'}
            bottom={'size-50'}
            position={'absolute'}
            alignItems={'center'}
            UNSAFE_className={classes.videoIndicator}
        >
            {formatCompactDuration(duration)}
        </Flex>
    );
};

export const MediaThumbnail = ({ onDoubleClick, onClick, url, alt, item }: MediaThumbnailProps) => {
    const src = useSettledSrc(url);

    return (
        <div onDoubleClick={onDoubleClick} onClick={onClick} className={classes.imgContainer}>
            <img src={src} alt={alt} className={classes.img} draggable={false} decoding='async' />
            {isVideo(item) && <VideoIndicator duration={item.duration} />}
        </div>
    );
};
