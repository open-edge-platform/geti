// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { RouterLink } from '@shared/components/router-link/router-link.component';

import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { useProjectStatus } from '../../../../core/projects/hooks/use-project-status.hook';
import { Performance, PerformanceType } from '../../../../core/projects/task.interface';
import { paths } from '../../../../core/services/routes';
import { AccuracyHalfDonutChart } from '../../../project-details/components/project-models/models-container/model-card/accuracy-container/accuracy-half-donut-chart';
import { AnomalyProjectPerformance } from './anomaly-project-performance.component';
import { ProjectPerformanceTooltip } from './project-performance-tooltip.component';

interface ProjectPerformanceProps {
    performance: Performance;
    projectIdentifier: ProjectIdentifier;
    isTaskChainProject: boolean;
}

export const ProjectPerformance = ({ performance, projectIdentifier, isTaskChainProject }: ProjectPerformanceProps) => {
    const { data: projectStatus } = useProjectStatus(projectIdentifier);

    return performance.type === PerformanceType.DEFAULT ? (
        <TooltipTrigger placement={'bottom'}>
            <RouterLink to={paths.project.models.index(projectIdentifier)}>
                <Flex direction='column' gap='size-100' height='size-400'>
                    <AccuracyHalfDonutChart
                        value={performance.score ?? 0}
                        size={'S'}
                        id={'navigation-toolbar-accuracy'}
                        ariaLabel='Project score'
                    />
                </Flex>
            </RouterLink>
            <Tooltip>
                <ProjectPerformanceTooltip
                    key={'performance'}
                    performance={projectStatus?.performance ?? performance}
                    isTaskChainProject={isTaskChainProject}
                />
            </Tooltip>
        </TooltipTrigger>
    ) : (
        <AnomalyProjectPerformance performance={performance} projectIdentifier={projectIdentifier} />
    );
};
