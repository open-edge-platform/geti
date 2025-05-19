// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMediaQuery } from '@geti/ui';

import { MediaItem } from '../../../../core/media/media.interface';
import { isLargeSizeQuery } from '../../../../theme/queries';
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
