// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { ActionButton, DialogTrigger, Tooltip, TooltipTrigger } from '@geti/ui';
import { isNil } from 'lodash-es';

import { useJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { NORMAL_INTERVAL, SLOW_INTERVAL } from '../../../../core/jobs/hooks/utils';
import { JobState } from '../../../../core/jobs/jobs.const';
import { FUX_NOTIFICATION_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../../core/user-settings/hooks/use-global-settings.hook';
import { useFirstWorkspaceIdentifier } from '../../../../providers/workspaces-provider/use-first-workspace-identifier.hook';
import { JobsDialog } from './jobs-dialog.component';
import { JobsIconWithNumber } from './jobs-icon-with-number/jobs-icon-with-number.component';

interface JobsActionIconProps {
    isDarkMode?: boolean;
}

export const JobsActionIcon = ({ isDarkMode = false }: JobsActionIconProps): JSX.Element => {
    const settings = useUserGlobalSettings();
    const { organizationId, workspaceId } = useFirstWorkspaceIdentifier();
    const runningJobsQuery = useJobs({ workspaceId, organizationId }).useGetJobs(
        {
            jobState: JobState.RUNNING,
        },
        {
            refetchInterval: (query) => {
                const hasRunningJobs = query.state.data?.pages[0].jobsCount.numberOfRunningJobs;

                return !isNil(hasRunningJobs) && hasRunningJobs > 0 ? NORMAL_INTERVAL : SLOW_INTERVAL;
            },
        }
    );
    const runningJobs = runningJobsQuery.data?.pages[0].jobsCount.numberOfRunningJobs || 0;

    const [isFullScreen, setIsFullScreen] = useState(false);

    return (
        <DialogTrigger type={isFullScreen ? 'fullscreen' : 'popover'} hideArrow>
            <TooltipTrigger placement={'bottom'}>
                <ActionButton
                    isQuiet
                    id='jobs-in-progress'
                    aria-label='Jobs in progress'
                    data-testid='jobs-in-progress'
                    colorVariant={isDarkMode ? 'dark' : 'light'}
                    onPress={() => {
                        settings.saveConfig({
                            ...settings.config,
                            [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: { isEnabled: false },
                        });
                    }}
                >
                    <JobsIconWithNumber runningJobs={runningJobs} isDarkMode={isDarkMode} />
                </ActionButton>
                <Tooltip>Jobs</Tooltip>
            </TooltipTrigger>
            {(close) => <JobsDialog onClose={close} isFullScreen={isFullScreen} setIsFullScreen={setIsFullScreen} />}
        </DialogTrigger>
    );
};
