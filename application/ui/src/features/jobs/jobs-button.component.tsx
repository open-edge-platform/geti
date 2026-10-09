// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { useTranslation } from '@/i18n';
import { ActionButton, Tooltip, TooltipTrigger } from '@geti-ui/ui';
import { useModelJobs } from 'hooks/api/jobs/jobs.hook';
import { useParams } from 'react-router';

import { ReactComponent as JobsIcon } from '../../assets/icons/jobs.svg';
import { ActiveJobsSync } from './active-jobs-sync.component';
import { JobsDialog } from './jobs-dialog/jobs-dialog.component';
import { ALL_PROJECTS, getStatusGroup } from './utils';

import classes from './jobs-button.module.scss';

const RunningJobIndicator = () => <span className={classes.runningIndicator} data-testid='running-job-indicator' />;

export const JobsButton = () => {
    const { t } = useTranslation();
    const { projectId } = useParams<{ projectId?: string }>();
    const { data: jobs = [] } = useModelJobs();
    const [isOpen, setIsOpen] = useState(false);

    const hasRunningJob = jobs.some((job) => getStatusGroup(job.status) === 'running');

    return (
        <>
            <ActiveJobsSync />
            <TooltipTrigger>
                <ActionButton isQuiet onPress={() => setIsOpen(true)} aria-label='Jobs'>
                    <span className={classes.iconWrapper}>
                        <JobsIcon />
                        {hasRunningJob && <RunningJobIndicator />}
                    </span>
                </ActionButton>
                <Tooltip>{t('common.labels.jobs')}</Tooltip>
            </TooltipTrigger>

            {isOpen && (
                <JobsDialog
                    initialProjectId={projectId ?? ALL_PROJECTS}
                    currentProjectId={projectId}
                    onClose={() => setIsOpen(false)}
                />
            )}
        </>
    );
};
