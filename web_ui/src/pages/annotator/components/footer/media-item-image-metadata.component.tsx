// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMediaQuery } from '@geti/ui';
import { isLargeSizeQuery } from '@geti/ui/theme';

import { MediaItem } from '../../../../core/media/media.interface';
import { LastAnnotator } from './last-annotator.component';
import { MediaNameAndResolution } from './media-name-and-resolution.component';

export const MediaItemImageMetadata = ({ mediaItem }: { mediaItem: MediaItem }): JSX.Element => {
    const { width, height } = mediaItem.metadata;
    const isLargeSize = useMediaQuery(isLargeSizeQuery);

    return (
        <>
            {mediaItem.lastAnnotatorId && (
                <LastAnnotator isLargeSize={isLargeSize} lastAnnotatorId={mediaItem.lastAnnotatorId} />
            )}

            <MediaNameAndResolution isLargeSize={isLargeSize} width={width} height={height} name={mediaItem.name} />
        </>
    );
};
