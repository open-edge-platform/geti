// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { ProjectProps } from '../../../../core/projects/project.interface';
import { ActionElement } from '../../../../shared/components/action-element/action-element.component';
import { formatPerformanceScore } from '../../../annotator/components/utils';

interface PerformanceProps {
    project: ProjectProps;
}

export const Performance = ({ project }: PerformanceProps) => {
    const tooltipText = 'The score percentage is the average of the scores of all active models.';

    const { performance } = project;

    if (performance.type === 'default_performance') {
        return (
            <TooltipTrigger placement={'bottom'}>
                <ActionElement>Score: {formatPerformanceScore(performance.score)}</ActionElement>
                <Tooltip>{tooltipText}</Tooltip>
            </TooltipTrigger>
        );
    }

    return (
        <Flex direction='column'>
            <TooltipTrigger placement={'bottom'}>
                <ActionElement>Image Score: {formatPerformanceScore(performance.globalScore)}</ActionElement>
                <Tooltip>{tooltipText}</Tooltip>
            </TooltipTrigger>
            <TooltipTrigger placement={'bottom'}>
                <ActionElement>Object Score: {formatPerformanceScore(performance.localScore)}</ActionElement>
                <Tooltip>{tooltipText}</Tooltip>
            </TooltipTrigger>
        </Flex>
    );
};
