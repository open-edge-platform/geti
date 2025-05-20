// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Tooltip, TooltipTrigger, View } from '@geti/ui';
import { Tag, TagHalf } from '@geti/ui/icons';

import { Video } from '../../../core/media/video.interface';
import { pluralize } from '../../utils';
import { QuietActionButton } from '../quiet-button/quiet-action-button.component';

import classes from './annotation-indicator.module.scss';

interface IndicatorProps {
    video: Video;
}

export const VideoAnnotationIndicator = ({ video }: IndicatorProps) => {
    const {
        identifier: { videoId },
        annotationStatistics,
    } = video;

    if (!annotationStatistics?.annotated && !annotationStatistics?.partiallyAnnotated) {
        return null;
    }

    const { annotated, partiallyAnnotated } = annotationStatistics;
    const state =
        annotated > 0 && partiallyAnnotated > 0 ? 'both' : annotated > 0 ? 'annotated' : 'partially_annotated';

    const tooltip =
        annotated > 0 && partiallyAnnotated > 0
            ? `
        ${pluralize(annotated, ' frame')} annotated
        ${pluralize(partiallyAnnotated, ' frame')} partially annotated
    `
            : annotated
              ? `${pluralize(annotated, ' frame')} annotated`
              : `${pluralize(partiallyAnnotated, ' frame')} partially annotated`;

    return (
        <View
            zIndex={10}
            right={'size-50'}
            bottom={'size-50'}
            position={'absolute'}
            borderRadius={'large'}
            backgroundColor={'gray-100'}
            UNSAFE_className={classes[state]}
            id={'annotation-state-indicator-id'}
            data-testid={'annotation-state-indicator-id'}
        >
            <TooltipTrigger placement={'bottom'}>
                <QuietActionButton
                    zIndex={4}
                    UNSAFE_className={classes.annotationIndicator}
                    id={'annotated-button-tooltip'}
                    aria-label={'annotation state indicator'}
                >
                    {annotated > 0 ? (
                        <Tag id={`${videoId}-annotated-remove-id`} />
                    ) : (
                        <TagHalf id={`${videoId}-annotated-remove-id`} />
                    )}
                </QuietActionButton>
                <Tooltip>{tooltip}</Tooltip>
            </TooltipTrigger>
        </View>
    );
};
