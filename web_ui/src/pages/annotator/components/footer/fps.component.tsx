// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { dimensionValue, useMediaQuery, useNumberFormatter, View } from '@geti/ui';
import { Fps } from '@geti/ui/icons';

import { biggerThanQuery } from '../../../../../packages/ui/theme/queries';
import { Video, VideoFrame } from '../../../../core/media/video.interface';

export const FPS = ({ mediaItem, className }: { mediaItem: Video | VideoFrame; className?: string }): JSX.Element => {
    const formatter = useNumberFormatter({
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
    const isBiggerThan1020px = useMediaQuery(biggerThanQuery('1020'));

    if (isNaN(mediaItem.metadata.fps)) {
        return <></>;
    }

    return (
        <View height='100%' paddingX={'size-100'} UNSAFE_className={className}>
            {isBiggerThan1020px && <Fps />}
            <span style={{ fontSize: dimensionValue('size-130') }} id='video-fps' aria-label='fps'>
                {formatter.format(mediaItem.metadata.fps)} fps
            </span>
        </View>
    );
};
