// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from 'react';

import { BottomProgressBar } from '@/components/bottom-progress-bar/bottom-progress-bar.component';
import { useTranslation } from '@/i18n';
import { Loading } from '@geti-ui/ui';
import { DATE_TIME_FORMAT, useFormatDate } from 'hooks/use-format-date.hook';

import { formatElapsed } from '../../utils';
import { JobActionsMenu } from './job-actions-menu.component';
import { JobRowLayout, type JobRowProps } from './job-row-layout.component';

export const RunningJobRow = ({ job, showStatusBadge, projectName, architectureName, onViewLogs }: JobRowProps) => {
    const { t } = useTranslation();
    const formatDateTime = useFormatDate(DATE_TIME_FORMAT);
    const { started_at, finished_at } = job;
    const [now, setNow] = useState(Date.now);

    useEffect(() => {
        if (!started_at || finished_at) {
            return;
        }

        const interval = window.setInterval(() => setNow(Date.now()), 1_000);

        return () => window.clearInterval(interval);
    }, [started_at, finished_at]);

    const startedAt = formatDateTime(started_at);
    const meta = [
        startedAt && t('jobs.meta.started', { time: startedAt }),
        t('jobs.meta.elapsed', { time: formatElapsed(job, now) }),
        job.progress > 0 && `${Math.round(job.progress)}%`,
    ]
        .filter(Boolean)
        .join(' · ');

    return (
        <BottomProgressBar progress={job.progress} color='var(--energy-blue)' ariaLabel={'Job progress'}>
            <JobRowLayout
                job={job}
                showStatusBadge={showStatusBadge}
                projectName={projectName}
                architectureName={architectureName}
                meta={meta}
                spinner={job.progress === 0 ? <Loading size={'S'} mode={'inline'} /> : undefined}
                actions={<JobActionsMenu job={job} canCancel={job.status === 'RUNNING'} onViewLogs={onViewLogs} />}
            />
        </BottomProgressBar>
    );
};
