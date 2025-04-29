// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Flex } from '@adobe/react-spectrum';

import { JobStep } from '../../../../core/jobs/jobs.interface';
import { JobListItemProgressStatus } from './jobs-list-item-progress.component';

interface JobProgressProps {
    step: JobStep;
    idPrefix: string;
}

export const JobProgress: FC<JobProgressProps> = ({ idPrefix, step }) => {
    return (
        <Flex alignItems={'center'} gap={'size-100'}>
            <Flex alignItems={'center'} flex={1} gap={'size-100'}>
                <JobListItemProgressStatus.Icon idPrefix={idPrefix} state={step.state} />
                <JobListItemProgressStatus.Message idPrefix={idPrefix} step={step} />
            </Flex>

            <JobListItemProgressStatus.StepState step={step} idPrefix={idPrefix} />

            <JobListItemProgressStatus.JobListItemFailedSkippedMessage idPrefix={idPrefix} step={step} />
        </Flex>
    );
};
