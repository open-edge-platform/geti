// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Flex, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

import { PressableElement } from '../../../../../../../shared/components/pressable-element/pressable-element.component';
import { AccuracyHalfDonutChart } from './accuracy-half-donut-chart';

interface AccuracyContainerProps {
    tooltip?: ReactNode;
    value: number | null;
    id?: string;
    heading: string;
    isDisabled?: boolean;
}

export const AccuracyContainer = ({
    tooltip = <></>,
    value,
    id,
    heading,
    isDisabled,
}: AccuracyContainerProps): JSX.Element => {
    return (
        <TooltipTrigger placement={'bottom'}>
            <PressableElement>
                <Flex
                    direction={'column'}
                    justifyContent={'center'}
                    alignItems={'center'}
                    data-testid={`accuracy-container-${id}`}
                    id={`accuracy-container-${id}`}
                    width='size-1250'
                    height='size-1250'
                >
                    {value === null ? (
                        <View UNSAFE_style={{ fontWeight: 'bold', textAlign: 'center' }}>{heading} not available</View>
                    ) : (
                        <AccuracyHalfDonutChart id={id} value={value} title={heading} isDisabled={isDisabled} />
                    )}
                </Flex>
            </PressableElement>
            <Tooltip>{tooltip}</Tooltip>
        </TooltipTrigger>
    );
};
