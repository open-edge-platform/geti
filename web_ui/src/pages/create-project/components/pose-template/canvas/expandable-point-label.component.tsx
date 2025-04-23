// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';
import clsx from 'clsx';
import { useHover, useNumberFormatter } from 'react-aria';

import { AiIcon } from '../../../../../assets/icons';
import { AnnotationLabel } from '../../../../../core/annotations/annotation.interface';
import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { isPrediction } from '../../../../../core/labels/utils';
import { useSelected } from '../../../../../providers/selected-provider/selected-provider.component';

import classes from './expandable-point-label.module.scss';

interface PointLabelProps {
    point: KeypointNode;
    isVisible: boolean;
    isFaded?: boolean;
    isOverlap?: boolean;
    children?: ReactNode;
    isOptionsEnabled?: boolean;
}

export const ExpandablePointLabel = ({
    point,
    isVisible,
    isFaded = false,
    isOverlap = false,
    isOptionsEnabled = true,
    children,
}: PointLabelProps) => {
    const { isSelected } = useSelected();
    const { hoverProps, isHovered } = useHover({});
    const formatter = useNumberFormatter({ style: 'percent', minimumFractionDigits: 0, maximumFractionDigits: 0 });

    const isActive = isHovered || isSelected(point.label.id);
    const labelTranslate = isOverlap ? 'translate(-12px, 10px)' : 'translate(-12px, calc(-100% - 12px))';
    // UI Todo: update KeypointNode with AnnotationLabel
    const isPredictionLabel = isPrediction(point.label as AnnotationLabel) && 'score' in point.label;

    if (!isVisible && !isActive) {
        return null;
    }

    return (
        <div {...hoverProps} className={clsx({ [classes.fadedLabel]: isFaded })} data-testid={'point label container'}>
            <Flex
                position={'absolute'}
                top={point.y}
                left={point.x}
                direction={'row'}
                width={'max-content'}
                minHeight={'size-400'}
                gap={'size-10'}
                UNSAFE_style={{
                    opacity: `var(--label-opacity)`,
                    transform: `scale(calc(1 / var(--zoom-level))) ${labelTranslate}`,
                    background: `var(--spectrum-global-color-gray-200)`,
                    borderRadius: `var(--spectrum-global-dimension-size-50)`,
                    transformOrigin: `top left`,
                }}
            >
                <Flex
                    gap={'size-50'}
                    alignItems={'center'}
                    data-testid={`pose label - ${point.label.name}`}
                    UNSAFE_style={{
                        borderRadius: 4,
                        color: 'var(--spectrum-global-color-static-black)',
                        padding: 'var(--spectrum-global-dimension-size-50) var(--spectrum-global-dimension-size-75)',
                        backgroundColor: `rgb(255 255 255 / ${isSelected(point.label.id) ? '88%' : '60%'})`,
                    }}
                >
                    {isPredictionLabel && <AiIcon width={16} aria-label={'prediction icon'} />}

                    <Text>{point.label.name}</Text>

                    {isPredictionLabel && <Text>{formatter.format(point.label.score as number)}</Text>}
                </Flex>

                {isActive && isOptionsEnabled && children}
            </Flex>
        </div>
    );
};
