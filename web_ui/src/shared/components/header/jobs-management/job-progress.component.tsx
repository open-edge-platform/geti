// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
