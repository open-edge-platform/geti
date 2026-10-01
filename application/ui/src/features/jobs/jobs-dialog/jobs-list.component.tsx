// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Grid, Heading, IllustratedMessage, Text } from '@geti-ui/ui';

import { ReactComponent as EmptyJobsImage } from '../../../assets/empty-dataset.svg';
import type { ModelJob } from '../utils';
import { JOB_GRID_COLUMNS, JobRow } from './job-row.component';

import classes from './jobs-dialog.module.scss';

interface JobsListProps {
    jobs: ModelJob[];
    isAllProjects: boolean;
    showStatusBadge: boolean;
    projectName: (projectId: string) => string;
    architectureName: (architectureId: string) => string;
    onViewLogs: (job: ModelJob) => void;
}

export const JobsList = ({
    jobs,
    isAllProjects,
    showStatusBadge,
    projectName,
    architectureName,
    onViewLogs,
}: JobsListProps) => {
    const { t } = useTranslation();
    const hasJobs = jobs.length > 0;

    return (
        <div aria-label='Jobs' className={classes.list}>
            {hasJobs && (
                <Grid
                    columns={JOB_GRID_COLUMNS}
                    columnGap={'size-200'}
                    UNSAFE_className={`${classes.grid} ${classes.header}`}
                >
                    <Text>{t('jobs.columns.name')}</Text>
                    <Text>{t('jobs.columns.type')}</Text>
                    <Text>{t('jobs.columns.architecture')}</Text>
                    <Text>{t('jobs.columns.device')}</Text>
                    <div />
                </Grid>
            )}
            {hasJobs ? (
                jobs.map((job) => (
                    <JobRow
                        key={job.job_id}
                        job={job}
                        showStatusBadge={showStatusBadge}
                        projectName={isAllProjects ? projectName(job.metadata.project.id) : undefined}
                        architectureName={architectureName(job.metadata.model.architecture)}
                        onViewLogs={() => onViewLogs(job)}
                    />
                ))
            ) : (
                <IllustratedMessage>
                    <EmptyJobsImage />
                    <Heading>{t('jobs.emptyState')}</Heading>
                </IllustratedMessage>
            )}
        </div>
    );
};
