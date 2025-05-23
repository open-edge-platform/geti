// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { Flex, Tooltip, TooltipTrigger } from '@geti/ui';
import { Pressable } from 'react-aria-components';
import { Link } from 'react-router-dom';

import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { useProjectStatus } from '../../../../core/projects/hooks/use-project-status.hook';
import { Performance, PerformanceType } from '../../../../core/projects/task.interface';
import { AccuracyHalfDonutChart } from '../../../project-details/components/project-models/models-container/model-card/accuracy-container/accuracy-half-donut-chart';
import { AnomalyProjectPerformance } from './anomaly-project-performance.component';
import { ProjectPerformanceTooltip } from './project-performance-tooltip.component';

import classes from './navigation-toolbar.module.scss';

interface ProjectPerformanceProps {
    performance: Performance;
    projectIdentifier: ProjectIdentifier;
    isTaskChainProject: boolean;
}

export const ProjectPerformance = ({ performance, projectIdentifier, isTaskChainProject }: ProjectPerformanceProps) => {
    const { data: projectStatus } = useProjectStatus(projectIdentifier);

    return performance.type === PerformanceType.DEFAULT ? (
        <TooltipTrigger placement={'bottom'}>
            <Pressable>
                <Link to={paths.project.models.index(projectIdentifier)} viewTransition>
                    <Flex
                        direction='column'
                        gap='size-100'
                        height='size-400'
                        UNSAFE_className={classes.performanceChart}
                    >
                        <AccuracyHalfDonutChart
                            value={performance.score ?? 0}
                            size={'S'}
                            id={'navigation-toolbar-accuracy'}
                            ariaLabel='Project score'
                        />
                    </Flex>
                </Link>
            </Pressable>
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
