// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Text } from '@geti/ui';

import { Performance } from '../../../../core/projects/task.interface';
import { formatPerformanceScore } from '../utils';

interface TooltipContentProps {
    performance: Performance;
    isTaskChainProject: boolean;
}

export const ProjectPerformanceTooltip = ({ performance, isTaskChainProject }: TooltipContentProps) => {
    if (performance.type === 'anomaly_performance') {
        return (
            <>
                <Text>Classification score: {formatPerformanceScore(performance.globalScore)}</Text>
                <br />
                <Text>Localization score: {formatPerformanceScore(performance.localScore)}</Text>
            </>
        );
    }

    if (isTaskChainProject) {
        return (
            <Text>
                The project score for a task-chain project is the average of the performance of the latest model for
                each task. Click here to go to the models page.
            </Text>
        );
    }

    return <Text>Latest project score</Text>;
};
