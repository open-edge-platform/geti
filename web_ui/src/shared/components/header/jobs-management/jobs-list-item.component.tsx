// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { ActionButton, Divider, Flex, Text, Tooltip, TooltipTrigger, View } from '@geti/ui';
import { isEmpty, isFunction } from 'lodash-es';
import { useNavigate } from 'react-router-dom';

import { Copy, DownloadIcon } from '../../../../assets/icons';
import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { JobType } from '../../../../core/jobs/jobs.const';
import { Job, JobExportStatus, JobProjectExportStatus } from '../../../../core/jobs/jobs.interface';
import {
    isJobDatasetExport,
    isJobOptimization,
    isJobProjectExport,
    isJobTest,
    isJobTrain,
} from '../../../../core/jobs/utils';
import { useApplicationServices } from '../../../../core/services/application-services-provider.component';
import { paths } from '../../../../core/services/routes';
import { useClipboard } from '../../../../hooks/use-clipboard/use-clipboard.hook';
import { useWorkspaceIdentifier } from '../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { downloadFile, formatDownloadUrl, sanitize } from '../../../utils';
import { QuietActionButton } from '../../quiet-button/quiet-action-button.component';
import { ActionLink } from './action-link.component';
import { JobListItemSkeletonLoader } from './job-list-item-skeleton-loader.component';
import { JobsDiscardAction } from './jobs-discard-action.component';
import { JobsListItemMetadata } from './jobs-list-item-metadata.component';
import { JobsListItemStatus } from './jobs-list-item-status.component';
import { DISCARD_TYPE, isJobExportDone, isJobFailed } from './utils';

import classes from './jobs.module.scss';

const DownloadExportButton = ({ job }: { job: JobExportStatus | JobProjectExportStatus }) => {
    const { router } = useApplicationServices();

    const src = router.PREFIX(formatDownloadUrl(String(job.metadata.downloadUrl)));

    const props =
        job.type === JobType.EXPORT_DATASET
            ? {
                  label: 'download dataset',
                  tooltip: 'Download dataset',
                  name: 'export_dataset',
              }
            : {
                  label: 'download project',
                  tooltip: 'Download project',
                  name: `${sanitize(job.metadata.project.name)}.zip`,
              };

    return (
        <TooltipTrigger placement={'bottom'}>
            <QuietActionButton
                height={'size-300'}
                marginEnd={'size-100'}
                aria-label={props.label}
                onPress={() => downloadFile(src, props.name)}
            >
                <DownloadIcon />
            </QuietActionButton>
            <Tooltip>{props.tooltip}</Tooltip>
        </TooltipTrigger>
    );
};

const CopyJobIdButton = ({ jobId }: { jobId: string }) => {
    const { copy } = useClipboard();
    const { workspaceId, organizationId } = useWorkspaceIdentifier();

    return (
        <TooltipTrigger placement={'bottom'}>
            <ActionButton
                aria-label='Copy job id'
                onPress={() =>
                    copy(JSON.stringify({ jobId, workspaceId, organizationId }), 'Job id copied successfully')
                }
            >
                <Copy />
            </ActionButton>
            <Tooltip>Copy full job id</Tooltip>
        </TooltipTrigger>
    );
};

interface JobsListItemProps {
    job: Job;
    expanded?: boolean;
    discardType?: DISCARD_TYPE;
    style?: CSSProperties;
    jobClickHandler?: () => void;
    onSelectItem: () => void;
}
export const JobsListItem = ({
    job,
    discardType,
    expanded = false,
    style = {},
    jobClickHandler,
    onSelectItem,
}: JobsListItemProps) => {
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();
    const navigate = useNavigate();
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { useDeleteJob, useCancelJob } = useJobs({ organizationId, workspaceId });

    const modelArchitecture =
        (isJobTest(job) && job.metadata.test.model.architectureName) ||
        ((isJobTrain(job) || isJobOptimization(job)) && job.metadata.task.modelArchitecture) ||
        undefined;

    const modelPrecision = isJobTest(job) ? job.metadata.test.model.precision[0] : undefined;

    const stepName = isJobTrain(job) ? job.metadata.task.name : undefined;

    const { projectId = '', projectName = '' } =
        'project' in job.metadata
            ? { projectName: job.metadata.project?.name, projectId: job.metadata.project?.id }
            : { projectName: '', projectId: '' };

    const optimizationType = isJobOptimization(job)
        ? job.metadata.optimizationType
        : isJobTest(job)
          ? job.metadata.test.model.optimizationType
          : undefined;

    const jobCost =
        FEATURE_FLAG_CREDIT_SYSTEM && job.cost
            ? {
                  requested: job.cost.requests.reduce((acc, v) => acc + v.amount, 0),
                  consumed: job.cost.consumed.reduce((acc, v) => acc + v.amount, 0),
              }
            : undefined;

    const handleActionLinkClick = () => {
        if (!projectId || isJobDatasetExport(job) || isJobProjectExport(job)) {
            return;
        }

        if (isJobTest(job)) {
            navigate(
                paths.project.tests.index({
                    organizationId,
                    projectId,
                    workspaceId,
                })
            );
        }

        if (isJobTrain(job)) {
            navigate(
                paths.project.models.index({
                    organizationId,
                    projectId,
                    workspaceId,
                })
            );
        }

        isFunction(jobClickHandler) && jobClickHandler();
    };

    if (useDeleteJob.isPending || useCancelJob.isPending) {
        return <JobListItemSkeletonLoader itemCount={1} style={{ marginTop: 0 }} />;
    }

    return (
        <View
            id={`job-scheduler-${job.id}`}
            data-testid={`job-scheduler-${job.id}`}
            borderRadius='regular'
            aria-label='Jobs list item'
            UNSAFE_style={style}
            UNSAFE_className={classes.jobsListItemWrapper}
        >
            <Flex
                alignItems='center'
                justifyContent='space-between'
                marginX='size-250'
                UNSAFE_style={{ paddingTop: 'var(--spectrum-global-dimension-size-250)' }}
            >
                <ActionLink
                    style={{ width: '100%' }}
                    inline={false}
                    isDisabled={!isFunction(jobClickHandler) || isEmpty(projectId)}
                    onPress={handleActionLinkClick}
                >
                    <Text
                        id={`job-scheduler-${job.id}-name`}
                        data-testid={`job-scheduler-${job.id}-name`}
                        UNSAFE_className={classes.jobName}
                    >
                        {job.name}
                    </Text>
                </ActionLink>
                <Flex alignItems={'center'}>
                    {isJobFailed(job) && <CopyJobIdButton jobId={job.id} />}
                    {isJobExportDone(job) && <DownloadExportButton job={job} />}
                    {discardType && (
                        <JobsDiscardAction
                            job={job}
                            discardType={discardType}
                            useCancelJob={useCancelJob}
                            useDeleteJob={useDeleteJob}
                        />
                    )}
                </Flex>
            </Flex>
            <Flex
                gap='size-600'
                alignItems='center'
                marginX='size-250'
                marginTop='size-100'
                marginBottom='size-150'
                UNSAFE_className={classes.jobMeta}
            >
                <JobsListItemMetadata
                    jobId={job.id}
                    stepName={stepName}
                    precision={modelPrecision}
                    projectName={projectName}
                    creationTime={job.creationTime}
                    architecture={modelArchitecture}
                    optimizationType={optimizationType}
                    cost={jobCost}
                />
            </Flex>

            <Divider size='S' marginX='size-250' />

            <JobsListItemStatus expanded={expanded} job={job} onExpandChange={onSelectItem} />
        </View>
    );
};
