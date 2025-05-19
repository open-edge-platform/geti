// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Grid, minmax, Text, useNumberFormatter } from '@adobe/react-spectrum';
import { usePress } from 'react-aria';

import { isVideo } from '../../../../core/media/video.interface';
import { TestMediaItem } from '../../../../core/tests/test-media.interface';
import { TestScore } from '../../../../core/tests/tests.interface';
import { MediaItemView } from '../../../../shared/components/media-item-view/media-item-view.component';
import { TruncatedText } from '../../../../shared/components/truncated-text/truncated-text.component';
import { getMediaId } from '../../../media/utils';
import { SCORE_FORMATTER_OPTIONS } from './utils';

import classes from './test-media-item-card.module.scss';

interface TestMediaItemDetailsCardProps {
    mediaItem: TestMediaItem;
    isSelected?: boolean;
    labelScore?: TestScore;
    shouldShowAnnotationIndicator: boolean;
    selectMediaItem: () => void;
}

export const TestMediaItemDetailsCard = ({
    mediaItem,
    isSelected = false,
    labelScore,
    shouldShowAnnotationIndicator,
    selectMediaItem,
}: TestMediaItemDetailsCardProps): JSX.Element => {
    const id = getMediaId(mediaItem.media);
    const scoreId = `${id}-score-id`;
    const isVideoItem = isVideo(mediaItem.media);
    const formatter = useNumberFormatter(SCORE_FORMATTER_OPTIONS);

    const { pressProps } = usePress({
        onPress: () => {
            !isVideoItem && selectMediaItem();
        },
    });

    return (
        <>
            <div
                id={id}
                className={`${classes.testMediaItemDetailsCard} ${isSelected ? classes.itemDetailsSelected : ''}`}
                {...pressProps}
            >
                <Grid
                    alignItems={'center'}
                    gap={'size-100'}
                    rows={['size-800']}
                    columns={['size-800', minmax('size-1000', '1fr'), 'max-content']}
                >
                    <MediaItemView
                        mediaItem={mediaItem.media}
                        shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                    />

                    <TruncatedText>{mediaItem.media.name}</TruncatedText>
                    <Text id={scoreId}>{formatter.format(Number(labelScore?.value))}</Text>
                </Grid>
            </div>
            <Divider size={'S'} />
        </>
    );
};
