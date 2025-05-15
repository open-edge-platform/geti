// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo, useState } from 'react';

import { Flex, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { LoadingIndicator } from '@geti/ui';
import { motion } from 'framer-motion';
import { maxBy } from 'lodash-es';

import { Alert, ChevronDownSmallLight } from '../../../../assets/icons';
import { JobStepState } from '../../../../core/jobs/jobs.const';
import { Job, JobStep } from '../../../../core/jobs/jobs.interface';
import { ANIMATION_PARAMETERS } from '../../../animation-parameters/animation-parameters';
import { isNonEmptyArray } from '../../../utils';
import { PressableElement } from '../../pressable-element/pressable-element.component';
import { QuietActionButton } from '../../quiet-button/quiet-action-button.component';
import { ThinProgressBar } from '../../thin-progress-bar/thin-progress-bar.component';
import { JobsListItemDetailedProgress } from './jobs-list-item-progress.component';
import { getJobDuration, getStepProgress, getStepProgressNumber } from './utils';

import classes from './jobs.module.scss';

interface JobsListItemStatusProps {
    job: Job;
    expanded?: boolean;
}

export const JobsListItemStatus = ({ expanded = false, job }: JobsListItemStatusProps): JSX.Element => {
    const [jobStepsExpanded, setJobStepsExpanded] = useState<boolean>(expanded);

    const onExpandHandler = () => {
        setJobStepsExpanded((prevState: boolean) => !prevState);
    };

    const stepToDisplay: JobStep | undefined = useMemo((): JobStep | undefined => {
        const jobsInProgress: JobStep[] = job.steps.filter(
            (step: JobStep): boolean => step.state === JobStepState.RUNNING
        );

        return maxBy(jobsInProgress, 'index');
    }, [job]);

    const jobWarning: JobStep | undefined = job.steps.find((step) => step.warning !== undefined);

    const jobDuration = getJobDuration(job);

    return (
        <>
            <Flex marginX='size-250' gap={'size-100'}>
                {!jobStepsExpanded && stepToDisplay !== undefined && (
                    <Flex flexGrow={1} flexShrink={0} alignItems='center' gap='size-100'>
                        <LoadingIndicator size='S' />
                        <Text>{`${stepToDisplay.stepName} (${stepToDisplay.index} of ${job.steps.length})`}</Text>
                    </Flex>
                )}
                {jobDuration !== undefined && (
                    <Flex alignItems={'center'}>
                        <Text id={`job-scheduler-${job.id}-job-duration`}>Completed in: {jobDuration}</Text>
                    </Flex>
                )}
                <Flex alignItems={'center'} justifyContent={'end'} flexGrow={1} flexShrink={1}>
                    {jobWarning !== undefined ? (
                        <TooltipTrigger placement={'bottom'}>
                            <PressableElement UNSAFE_style={{ display: 'flex' }}>
                                <Alert aria-label={'Job step alert'} className={classes.warningSectionIcon} />
                            </PressableElement>
                            <Tooltip>{jobWarning.warning?.trim()}</Tooltip>
                        </TooltipTrigger>
                    ) : null}

                    {!jobStepsExpanded && stepToDisplay?.progress ? (
                        <Text id={`job-scheduler-${job.id}-progress`} data-testid={`job-scheduler-${job.id}-progress`}>
                            {getStepProgress(stepToDisplay.progress)}
                        </Text>
                    ) : null}
                </Flex>
                <Flex alignItems='center' marginY='size-100'>
                    {isNonEmptyArray(job.steps) && (
                        <Flex justifyContent={'space-between'} alignItems={'center'}>
                            <QuietActionButton
                                id={`job-scheduler-${job.id}-action-expand`}
                                data-testid={`job-scheduler-${job.id}-action-expand`}
                                onPress={onExpandHandler}
                                aria-expanded={jobStepsExpanded}
                            >
                                <motion.div
                                    animate={{ rotate: jobStepsExpanded ? -180 : 0 }}
                                    style={{ position: 'relative', width: '24px', height: '24px' }}
                                >
                                    <View position={'absolute'}>
                                        <ChevronDownSmallLight width={24} height={24} />
                                    </View>
                                </motion.div>
                            </QuietActionButton>
                        </Flex>
                    )}
                </Flex>
            </Flex>
            {!jobStepsExpanded && stepToDisplay && (
                <ThinProgressBar
                    id={`job-scheduler-${job.id}-progress-bar`}
                    size={'size-25'}
                    customColor={'var(--energy-blue-shade)'}
                    progress={getStepProgressNumber(stepToDisplay.progress)}
                />
            )}
            {jobStepsExpanded && (
                <motion.div variants={ANIMATION_PARAMETERS.ANIMATE_LIST} initial={'hidden'} animate={'visible'}>
                    <View paddingX={'size-150'} paddingBottom={'size-150'}>
                        <View
                            id={`job-scheduler-${job.id}-step-list`}
                            backgroundColor={'gray-50'}
                            paddingBottom={'size-100'}
                        >
                            {job.steps.map((step: JobStep) => (
                                <JobsListItemDetailedProgress key={step.index} job={job} step={step} />
                            ))}
                        </View>
                    </View>
                </motion.div>
            )}
        </>
    );
};
