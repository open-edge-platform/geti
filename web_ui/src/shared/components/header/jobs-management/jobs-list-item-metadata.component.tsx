// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import isNil from 'lodash/isNil';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { formatJobsCreationTime, isNonEmptyString, pluralize } from '../../../utils';
import { ActionElement } from '../../action-element/action-element.component';
import { DomainName } from '../../domain-name/domain-name.component';
import { TruncatedTextWithTooltip } from '../../truncated-text/truncated-text.component';
import { getNameFromJob } from './utils';

import classes from './jobs.module.scss';

export interface JobsListItemMetadataProps {
    jobId: string;
    projectName: string;
    creationTime: string;
    stepName?: string;
    precision?: string;
    architecture?: string;
    optimizationType?: string;
    cost?: {
        requested: number;
        consumed: number;
    };
}

export const JobsListItemMetadata = ({
    jobId,
    projectName,
    creationTime,
    stepName,
    precision,
    architecture,
    optimizationType,
    cost,
}: JobsListItemMetadataProps) => {
    const stepNameFromJob: string | undefined = stepName ? getNameFromJob(stepName) : undefined;
    const creationDate: string = formatJobsCreationTime(creationTime);

    return (
        <Flex
            alignItems={'center'}
            justifyContent={'space-between'}
            width={'100%'}
            gap={'size-250'}
            UNSAFE_className={classes.meta}
        >
            {isNonEmptyString(projectName) && (
                <View flex={1}>
                    <TruncatedTextWithTooltip id={`job-scheduler-${jobId}-meta-project-name`}>
                        {`Project: ${projectName}`}
                    </TruncatedTextWithTooltip>
                </View>
            )}
            <View flex={1}>
                {isNonEmptyString(architecture) && (
                    <TruncatedTextWithTooltip id={`job-scheduler-${jobId}-meta-architecture`}>
                        {`Architecture: ${architecture}`}
                    </TruncatedTextWithTooltip>
                )}
            </View>
            {isNil(precision) && (
                <View flex={1}>
                    {isNonEmptyString(stepNameFromJob) && (
                        <TruncatedTextWithTooltip
                            id={`job-scheduler-${jobId}-meta-task-name`}
                            data-testid={`job-scheduler-${jobId}-meta-task-name`}
                        >
                            Task: <DomainName domain={stepNameFromJob as DOMAIN} />
                        </TruncatedTextWithTooltip>
                    )}
                </View>
            )}
            <View flex={1}>
                {isNonEmptyString(optimizationType) && (
                    <TruncatedTextWithTooltip id={`job-scheduler-${jobId}-meta-optimization-type`}>
                        {`Optimization type: ${optimizationType}`}
                    </TruncatedTextWithTooltip>
                )}
            </View>
            {isNonEmptyString(precision) && (
                <View flex={1}>
                    <TruncatedTextWithTooltip id={`job-scheduler-${jobId}-meta-precision`}>
                        {`Precision: ${precision}`}
                    </TruncatedTextWithTooltip>
                </View>
            )}
            {cost && (
                <View flex={1}>
                    <TooltipTrigger placement='bottom'>
                        <ActionElement id={`job-scheduler-${jobId}-meta-cost`} isTruncated>
                            {`Cost: ${pluralize(cost.requested, 'credit')} `}
                        </ActionElement>
                        <Tooltip>
                            {`Credits requested: ${cost.requested}`}
                            <br />
                            {`Credits consumed: ${cost.consumed}`}
                        </Tooltip>
                    </TooltipTrigger>
                </View>
            )}
            <View flex={1}>
                <TruncatedTextWithTooltip id={`job-scheduler-${jobId}-meta-created-time`}>
                    {`Created: ${creationDate}`}
                </TruncatedTextWithTooltip>
            </View>
        </Flex>
    );
};
