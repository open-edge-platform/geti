// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
