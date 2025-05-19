// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Tooltip, TooltipTrigger, View } from '@geti/ui';

import { Revisit, Tag, TagHalf } from '../../../assets/icons';
import { MEDIA_ANNOTATION_STATUS } from '../../../core/media/base.interface';

import classes from './annotation-indicator.module.scss';

interface IndicatorProps {
    id: string;
    state?: MEDIA_ANNOTATION_STATUS;

    annotatedTooltip: string;
    revisitTooltip: string;
    partiallyAnnotatedTooltip: string;
}

export const StateIndicator = ({
    id,
    state,
    annotatedTooltip,
    partiallyAnnotatedTooltip,
    revisitTooltip,
}: IndicatorProps) => {
    if (!state || state === MEDIA_ANNOTATION_STATUS.NONE) return <></>;

    return (
        <View
            id={'annotation-state-indicator-id'}
            data-testid={'annotation-state-indicator-id'}
            position='absolute'
            right={'size-50'}
            bottom={'size-50'}
            backgroundColor='gray-100'
            borderRadius='large'
            zIndex={10}
            UNSAFE_className={classes[state]}
        >
            {state === MEDIA_ANNOTATION_STATUS.PARTIALLY_ANNOTATED && (
                <TooltipTrigger placement={'bottom'}>
                    <ActionButton
                        isQuiet
                        id={'partially-annotated-button-tooltip'}
                        aria-label={'Partially annotated'}
                        UNSAFE_className={classes.annotationIndicator}
                    >
                        <TagHalf id={`${id}-remove-id`} />
                    </ActionButton>
                    <Tooltip>{partiallyAnnotatedTooltip}</Tooltip>
                </TooltipTrigger>
            )}
            {state === MEDIA_ANNOTATION_STATUS.ANNOTATED && (
                <TooltipTrigger placement={'bottom'}>
                    <ActionButton
                        isQuiet
                        id={'annotated-button-tooltip'}
                        aria-label={'Annotated'}
                        UNSAFE_className={classes.annotationIndicator}
                    >
                        <Tag id={`${id}-checkmark-id`} />
                    </ActionButton>
                    <Tooltip>{annotatedTooltip}</Tooltip>
                </TooltipTrigger>
            )}
            {state === MEDIA_ANNOTATION_STATUS.TO_REVISIT && (
                <TooltipTrigger placement={'bottom'}>
                    <ActionButton
                        id={'revisit-button-tooltip'}
                        aria-label='Revisit annotation'
                        UNSAFE_className={classes.annotationIndicator}
                    >
                        <Revisit id={`${id}-revisit-id`} />
                    </ActionButton>
                    <Tooltip>{revisitTooltip}</Tooltip>
                </TooltipTrigger>
            )}
        </View>
    );
};
