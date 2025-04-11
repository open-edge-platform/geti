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

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { useProjectStatus } from '../../../../core/projects/hooks/use-project-status.hook';
import { Performance, PerformanceType } from '../../../../core/projects/task.interface';
import { paths } from '../../../../core/services/routes';
import { RouterLink } from '../../../../shared/components/router-link/router-link.component';
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
