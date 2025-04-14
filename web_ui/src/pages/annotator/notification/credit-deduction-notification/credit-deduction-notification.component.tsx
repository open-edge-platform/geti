// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { InfiniteData } from '@tanstack/react-query';

import { useGetScheduledJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { JobTask } from '../../../../core/jobs/jobs.interface';
import { JobsResponse } from '../../../../core/jobs/services/jobs-service.interface';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { FUX_NOTIFICATION_KEYS, FUX_SETTINGS_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { UserGlobalSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { getSettingsOfType } from '../../../../core/user-settings/utils';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { useIsAutoTrainingOn } from '../../hooks/use-is-auto-training-on.hook';
import { JOB_TRIGGER, onScheduledTrainingJobs } from '../utils';

interface CreditDeductionNotificationProps {
    settings: UseSettings<UserGlobalSettings>;
}

const useCreditDeductionNotificationJobs = ({
    projectIdentifier,
    enabled,
    onSuccess,
}: {
    projectIdentifier: ProjectIdentifier;
    enabled: boolean;
    onSuccess: (jobs: InfiniteData<JobsResponse>) => void;
}) => {
    const handleSuccessRef = useRef(onSuccess);

    const jobsQuery = useGetScheduledJobs({ projectId: projectIdentifier.projectId, queryOptions: { enabled } });

    useEffect(() => {
        handleSuccessRef.current = onSuccess;
    }, [onSuccess]);

    useEffect(() => {
        if (!enabled || !jobsQuery.isSuccess) {
            return;
        }

        handleSuccessRef.current(jobsQuery.data);
    }, [enabled, jobsQuery.data, jobsQuery.isSuccess]);
};

export const CreditDeductionNotification = ({ settings }: CreditDeductionNotificationProps): JSX.Element => {
    const openedNotification = useRef(new Set<string>());
    const { addNotification } = useNotification();

    const { project, projectIdentifier } = useProject();
    const isAutoTrainingOn = useIsAutoTrainingOn({ project, projectIdentifier });

    const fuxConfig = getSettingsOfType(settings.config, {
        ...FUX_NOTIFICATION_KEYS,
        ...FUX_SETTINGS_KEYS,
    });
    const isAutoTrainingFirstModalEnabled = fuxConfig[FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]?.isEnabled;
    const isAutoTrainingNotificationEnabled = fuxConfig[FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]?.isEnabled;
    const firstAutoTrainingJobId = fuxConfig.firstAutoTrainingJobId.value;
    const isQueryEnabled = Boolean(
        !isAutoTrainingFirstModalEnabled && !isAutoTrainingNotificationEnabled && isAutoTrainingOn
    );

    useCreditDeductionNotificationJobs({
        projectIdentifier,
        enabled: isQueryEnabled,
        onSuccess: onScheduledTrainingJobs((scheduledJob) => {
            const jobTask = scheduledJob as JobTask;
            const totalCreditsToConsume = jobTask.cost?.requests.reduce((acc, c) => acc + c.amount, 0) || 0;

            if (
                !isQueryEnabled ||
                !totalCreditsToConsume ||
                openedNotification.current.has(scheduledJob.id) ||
                firstAutoTrainingJobId === scheduledJob.id
            ) {
                return;
            }

            openedNotification.current.add(scheduledJob.id);
            addNotification({
                message: `Auto-training round has been started, ${totalCreditsToConsume} credits deducted.`,
                type: NOTIFICATION_TYPE.INFO,
            });
        }, JOB_TRIGGER.AUTO),
    });

    return <></>;
};
