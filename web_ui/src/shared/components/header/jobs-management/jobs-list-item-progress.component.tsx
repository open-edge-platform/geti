// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Flex, Loading, Text, View } from '@geti/ui';
import { CanceledIcon, CheckCircleOutlined, ExclamationCircleOutlined, SkippedIcon, WaitingIcon } from '@geti/ui/icons';
import { COLOR_MODE } from '@geti/ui/theme';
import { isEmpty } from 'lodash-es';

import { JobStepState } from '../../../../core/jobs/jobs.const';
import { Job, JobStep } from '../../../../core/jobs/jobs.interface';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { ThinProgressBar } from '../../thin-progress-bar/thin-progress-bar.component';
import { getStepProgress, getStepProgressNumber } from './utils';

import classes from './jobs.module.scss';

interface JobsListItemDetailedProgressProps {
    job: Job;
    step: JobStep;
}

const getStepState = (state: JobStepState, step: JobStep): string => {
    switch (state) {
        case JobStepState.FAILED:
            return 'Failed';
        case JobStepState.CANCELLED:
            return 'Cancelled';
        case JobStepState.SKIPPED:
            return 'Skipped';
        case JobStepState.WAITING:
            return 'Waiting...';
        default:
            return getStepProgress(step.progress);
    }
};

const getStepStateColor = (state: string): string => {
    switch (state) {
        case JobStepState.RUNNING:
            return COLOR_MODE.INFORMATIVE;
        case JobStepState.FINISHED:
            return COLOR_MODE.POSITIVE;
        case JobStepState.FAILED:
            return COLOR_MODE.NEGATIVE;
        case JobStepState.SKIPPED:
            return COLOR_MODE.WARNING;
        default:
            return 'var(--spectrum-global-color-gray-400)';
    }
};

const getStepStateIcon = (state: string): JSX.Element => {
    switch (state) {
        case JobStepState.RUNNING:
            return <Loading mode='inline' size='S' />;
        case JobStepState.FINISHED:
            return <CheckCircleOutlined className={classes.iconFinished} />;
        case JobStepState.FAILED:
            return <ExclamationCircleOutlined className={classes.iconFailed} />;
        case JobStepState.CANCELLED:
            return <CanceledIcon className={classes.iconCanceled} />;
        case JobStepState.SKIPPED:
            return <SkippedIcon className={classes.iconSkipped} />;
        case JobStepState.WAITING:
            return <WaitingIcon className={classes.iconWaiting} />;
        default:
            return <></>;
    }
};

const isFailedOrSkippedState = (state: string) => state === JobStepState.FAILED || state === JobStepState.SKIPPED;

const getStepMessage = (step: JobStep) => {
    if (isFailedOrSkippedState(step.state) || isEmpty(step.message)) {
        return '';
    }

    return `: ${step.message}`;
};

interface JobListItemProgressMessageProps {
    idPrefix: string;
    step: JobStep;
    numberOfSteps: number;
}

const Icon: FC<{ state: JobStepState; idPrefix: string }> = ({ state, idPrefix }) => {
    return (
        <View
            width={'size-200'}
            height={'size-200'}
            id={`${idPrefix}-state-icon`}
            data-testid={`${idPrefix}-state-icon`}
        >
            {getStepStateIcon(state)}
        </View>
    );
};

const Message: FC<Omit<JobListItemProgressMessageProps, 'numberOfSteps'>> = ({ idPrefix, step }) => {
    return (
        <Text
            id={`${idPrefix}-name`}
            data-testid={`${idPrefix}-name`}
        >{`${step.stepName}${getStepMessage(step)}`}</Text>
    );
};

const MessageWithSteps: FC<JobListItemProgressMessageProps> = ({ idPrefix, step, numberOfSteps }) => {
    return (
        <Text
            id={`${idPrefix}-name`}
            data-testid={`${idPrefix}-name`}
        >{`${step.stepName} (${step.index} of ${numberOfSteps})${getStepMessage(step)}`}</Text>
    );
};

const StepState: FC<{ idPrefix: string; step: JobStep }> = ({ idPrefix, step }) => {
    return (
        <Text id={`${idPrefix}-progress`} data-testid={`${idPrefix}-progress`}>
            {getStepState(step.state, step)}
        </Text>
    );
};

const JobListItemFailedSkippedMessage: FC<{ idPrefix: string; step: JobStep }> = ({ idPrefix, step }) => {
    return isFailedOrSkippedState(step.state) && !isEmpty(step.message) ? (
        <View
            id={`${idPrefix}-message`}
            data-testid={`${idPrefix}-message`}
            paddingX={'size-100'}
            paddingY={'size-50'}
            UNSAFE_className={`${classes.stepMessage} ${classes[step.state.toLowerCase()]}`}
        >
            <Text>{step.message}</Text>
        </View>
    ) : (
        <></>
    );
};

export const JobListItemProgressStatus = {
    JobListItemFailedSkippedMessage,
    StepState,
    Icon,
    MessageWithSteps,
    Message,
};

export const JobsListItemDetailedProgress = ({ job, step }: JobsListItemDetailedProgressProps) => {
    const idPrefix = `job-scheduler-${job.id}-step-${step.index}-${idMatchingFormat(step.stepName)}`;
    return (
        <View
            id={idPrefix}
            paddingX={'size-100'}
            paddingTop={'size-150'}
            backgroundColor={'gray-50'}
            data-testid={idPrefix}
        >
            <Flex alignItems='center' justifyContent='space-between' marginX={'size-50'} gap={'size-50'}>
                <Flex alignItems='center' gap='size-100'>
                    <Icon idPrefix={idPrefix} state={step.state} />
                    <MessageWithSteps idPrefix={idPrefix} step={step} numberOfSteps={job.steps.length} />
                </Flex>
                <StepState idPrefix={idPrefix} step={step} />
            </Flex>

            <JobListItemFailedSkippedMessage step={step} idPrefix={idPrefix} />

            {!isFailedOrSkippedState(step.state) && (
                <ThinProgressBar
                    id={`${idPrefix}-progress-bar`}
                    size={'size-25'}
                    marginTop={'size-50'}
                    progress={getStepProgressNumber(step.progress)}
                    customColor={getStepStateColor(step.state)}
                    completed={isFailedOrSkippedState(step.state)}
                />
            )}
        </View>
    );
};
