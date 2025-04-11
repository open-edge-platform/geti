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

import { ReactNode } from 'react';

import { Flex, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

import { ActionElement } from '../../../../../../../shared/components/action-element/action-element.component';
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
            <ActionElement>
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
                        <View UNSAFE_style={{ fontWeight: 'bold', textAlign: 'center' }}>
                            {heading} is not available
                        </View>
                    ) : (
                        <AccuracyHalfDonutChart id={id} value={value} title={heading} isDisabled={isDisabled} />
                    )}
                </Flex>
            </ActionElement>
            <Tooltip>{tooltip}</Tooltip>
        </TooltipTrigger>
    );
};
