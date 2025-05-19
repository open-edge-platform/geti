// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, PressableElement, Tooltip, TooltipTrigger } from '@geti/ui';

import { Performance, PerformanceType, Score } from '../../../../../../../core/projects/task.interface';
import { AccuracyHalfDonutChart } from '../../../../../../project-details/components/project-models/models-container/model-card/accuracy-container/accuracy-half-donut-chart';

interface ProjectPerformanceProps {
    performance: Performance;
}

interface ProjectPerformanceDetailsProps {
    score: Score | null;
    title: string;
    id: string;
}

const ProjectPerformanceDetails = ({ score, title, id }: ProjectPerformanceDetailsProps): JSX.Element => {
    if (score === null) {
        return <></>;
    }

    return (
        <TooltipTrigger placement={'bottom'}>
            <PressableElement width={'100%'} height={'100%'}>
                <AccuracyHalfDonutChart id={id} value={score.value} size={'S'} ariaLabel={title} />
            </PressableElement>
            <Tooltip>{title}</Tooltip>
        </TooltipTrigger>
    );
};

export const ProjectPerformance = ({ performance }: ProjectPerformanceProps): JSX.Element => {
    if (performance.score === null) {
        return <></>;
    }

    if (performance.type === PerformanceType.DEFAULT) {
        const isTaskChainProject = performance.taskPerformances.length > 1;

        return (
            <Flex alignItems={'center'} gap={'size-100'} marginEnd={'size-100'} height={'size-400'}>
                {performance.taskPerformances.map(({ score, taskNodeId, domain }) => {
                    return (
                        <ProjectPerformanceDetails
                            title={
                                isTaskChainProject
                                    ? `${domain} - metric type: ${score?.metricType}`
                                    : `Metric type: ${score?.metricType}`
                            }
                            id={taskNodeId}
                            key={taskNodeId}
                            score={score}
                        />
                    );
                })}
            </Flex>
        );
    }

    const [taskPerformance] = performance.taskPerformances;
    const { globalScore, localScore } = taskPerformance;

    const localTitle = `Object score metric type: ${localScore?.metricType}`;
    const globalTitle = `Image score metric type: ${globalScore?.metricType}`;

    return (
        <Flex alignItems={'center'} gap={'size-100'} marginEnd={'size-100'} height={'size-400'}>
            <ProjectPerformanceDetails
                id={taskPerformance.taskNodeId}
                key={globalTitle}
                title={globalTitle}
                score={globalScore}
            />
            <ProjectPerformanceDetails
                id={taskPerformance.taskNodeId}
                key={localTitle}
                title={localTitle}
                score={localScore}
            />
        </Flex>
    );
};
