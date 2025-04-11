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

import { useNumberFormatter, View } from '@adobe/react-spectrum';
import { usePress } from 'react-aria';

import { isVideo } from '../../../../core/media/video.interface';
import { TestMediaItem } from '../../../../core/tests/test-media.interface';
import { TestScore } from '../../../../core/tests/tests.interface';
import { IndicatorWrapper } from '../../../../shared/components/indicator-wrapper/indicator-wrapper.component';
import { MediaItemView } from '../../../../shared/components/media-item-view/media-item-view.component';
import { getMediaId } from '../../../media/utils';
import { SCORE_FORMATTER_OPTIONS } from './utils';

import classes from './test-media-item-card.module.scss';

const SELECTED_PROPS = Object.freeze({ borderColor: 'informative', borderWidth: 'thick' });

interface TestMediaItemCardProps {
    mediaItem: TestMediaItem;
    isSelected?: boolean;
    labelScore?: TestScore;
    shouldShowAnnotationIndicator: boolean;
    selectMediaItem: () => void;
}

export const TestMediaItemCard = ({
    mediaItem,
    isSelected = false,
    labelScore,
    shouldShowAnnotationIndicator,
    selectMediaItem,
}: TestMediaItemCardProps): JSX.Element => {
    const isVideoItem = isVideo(mediaItem.media);
    const formatter = useNumberFormatter(SCORE_FORMATTER_OPTIONS);

    const { pressProps } = usePress({
        onPress: () => {
            // Don't show 'Preview modal' with videos
            !isVideoItem && selectMediaItem();
        },
    });

    const id = getMediaId(mediaItem.media);
    const scoreId = `${id}-score-id`;
    const selectedProps = isSelected ? SELECTED_PROPS : {};

    return (
        <View
            position='relative'
            height='100%'
            width='100%'
            UNSAFE_className={classes.mediaItemCard}
            {...selectedProps}
        >
            <div
                id={id}
                style={{ position: 'relative', width: 'inherit', height: 'inherit', cursor: 'pointer' }}
                {...pressProps}
            >
                <IndicatorWrapper top={'size-50'} left={'size-50'} UNSAFE_className={classes.imageScore} id={scoreId}>
                    {formatter.format(Number(labelScore?.value))}
                </IndicatorWrapper>

                <MediaItemView
                    mediaItem={mediaItem.media}
                    shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                />
            </div>
        </View>
    );
};
