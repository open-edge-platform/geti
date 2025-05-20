// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Content, Dialog, DialogTrigger, Divider, Flex, Heading, Text, Tooltip, TooltipTrigger } from '@geti/ui';
import { ScoreMetric } from '@geti/ui/icons';

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
