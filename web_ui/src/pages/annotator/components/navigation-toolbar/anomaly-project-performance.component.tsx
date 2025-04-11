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

import {
    Content,
    Dialog,
    DialogTrigger,
    Divider,
    Flex,
    Heading,
    Text,
    Tooltip,
    TooltipTrigger,
} from '@adobe/react-spectrum';

import { ScoreMetric } from '../../../../assets/icons';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { AnomalyTaskPerformance } from '../../../../core/projects/task.interface';
import { ColorMode, QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { AnomalyProjectPerformanceChart } from './anomaly-project-performance-chart.component';
import { ProjectPerformanceTooltip } from './project-performance-tooltip.component';

import classes from './navigation-toolbar.module.scss';

interface AnomalyProjectPerformanceProps {
    performance: AnomalyTaskPerformance;
    projectIdentifier: ProjectIdentifier;
}

export const AnomalyProjectPerformance = ({
    performance,
    projectIdentifier,
}: AnomalyProjectPerformanceProps): JSX.Element => {
    return (
        <DialogTrigger type='popover' hideArrow>
            <TooltipTrigger placement={'bottom'}>
                <QuietActionButton colorMode={ColorMode.DARK} aria-label={'project performance'}>
                    <ScoreMetric className={classes.anomalyPerformanceIcon} />
                </QuietActionButton>
                <Tooltip>
                    <ProjectPerformanceTooltip
                        key={'performance'}
                        performance={performance}
                        isTaskChainProject={false}
                    />
                </Tooltip>
            </TooltipTrigger>

            <Dialog>
                <Heading>
                    <Flex alignItems={'center'} justifyContent={'space-between'}>
                        <Text>Project performance</Text>
                        <Text UNSAFE_className={classes.anomalyPerformanceActiveModel}>Active model</Text>
                    </Flex>
                </Heading>
                <Divider />
                <Content UNSAFE_style={{ overflowY: 'hidden' }} height={'size-1250'}>
                    <Flex alignItems={'center'} justifyContent={'space-around'} gap={'size-200'}>
                        <AnomalyProjectPerformanceChart
                            score={performance.localScore}
                            label={'Image score'}
                            projectIdentifier={projectIdentifier}
                        />
                        <AnomalyProjectPerformanceChart
                            score={performance.globalScore}
                            label={'Object score'}
                            projectIdentifier={projectIdentifier}
                        />
                    </Flex>
                </Content>
            </Dialog>
        </DialogTrigger>
    );
};
