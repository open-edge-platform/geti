// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import isNil from 'lodash/isNil';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { formatJobsCreationTime, isNonEmptyString, pluralize } from '../../../utils';
import { DomainName } from '../../domain-name/domain-name.component';
import { PressableElement } from '../../pressable-element/pressable-element.component';
import { TruncatedText, TruncatedTextWithTooltip } from '../../truncated-text/truncated-text.component';
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
                        <PressableElement id={`job-scheduler-${jobId}-meta-cost`}>
                            <TruncatedText>{`Cost: ${pluralize(cost.requested, 'credit')} `}</TruncatedText>
                        </PressableElement>
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
