// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { PressableElement } from '@shared/components/pressable-element/pressable-element.component';

import { ProjectProps } from '../../../../core/projects/project.interface';
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
                <PressableElement>Score: {formatPerformanceScore(performance.score)}</PressableElement>
                <Tooltip>{tooltipText}</Tooltip>
            </TooltipTrigger>
        );
    }

    return (
        <Flex direction='column'>
            <TooltipTrigger placement={'bottom'}>
                <PressableElement>Image Score: {formatPerformanceScore(performance.globalScore)}</PressableElement>
                <Tooltip>{tooltipText}</Tooltip>
            </TooltipTrigger>
            <TooltipTrigger placement={'bottom'}>
                <PressableElement>Object Score: {formatPerformanceScore(performance.localScore)}</PressableElement>
                <Tooltip>{tooltipText}</Tooltip>
            </TooltipTrigger>
        </Flex>
    );
};
