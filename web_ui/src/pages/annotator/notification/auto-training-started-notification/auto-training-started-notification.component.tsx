// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { InfiniteData } from '@tanstack/react-query';

import { useGetScheduledJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
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

interface AutoTrainingStartedNotificationProps {
    settings: UseSettings<UserGlobalSettings>;
}

const useAutoTrainingStartedNotificationJobs = ({
    enabled,
    projectIdentifier,
    onSuccess,
}: {
    enabled: boolean;
    projectIdentifier: ProjectIdentifier;
    onSuccess: (data: InfiniteData<JobsResponse>) => void;
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
    }, [enabled, jobsQuery.isSuccess, jobsQuery.data]);
};

export const AutoTrainingStartedNotification = ({ settings }: AutoTrainingStartedNotificationProps): JSX.Element => {
    const openedNotification = useRef(new Set<string>());
    const { addNotification } = useNotification();

    const { project, projectIdentifier } = useProject();
    const isAutoTrainingOn = useIsAutoTrainingOn({ project, projectIdentifier });

    const fuxSettingsAndNotificationsConfig = getSettingsOfType(settings.config, {
        ...FUX_SETTINGS_KEYS,
        ...FUX_NOTIFICATION_KEYS,
        ...FUX_SETTINGS_KEYS,
    });
    const firstAutoTrainingJobId = fuxSettingsAndNotificationsConfig.firstAutoTrainingJobId.value;
    const queryEnabled =
        isAutoTrainingOn &&
        !fuxSettingsAndNotificationsConfig.neverAutotrained.value &&
        !fuxSettingsAndNotificationsConfig.annotatorAutoTrainingStarted.isEnabled;

    useAutoTrainingStartedNotificationJobs({
        enabled: queryEnabled,
        projectIdentifier,
        onSuccess: onScheduledTrainingJobs((scheduledJob) => {
            if (
                !queryEnabled ||
                firstAutoTrainingJobId === scheduledJob.id ||
                openedNotification.current.has(scheduledJob.id)
            ) {
                return;
            }

            openedNotification.current.add(scheduledJob.id);
            addNotification({ message: `Auto-training round has been started.`, type: NOTIFICATION_TYPE.INFO });
        }, JOB_TRIGGER.AUTO),
    });

    return <></>;
};
