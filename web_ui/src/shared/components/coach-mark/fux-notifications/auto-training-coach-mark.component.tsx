// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, useCallback, useEffect } from 'react';

import { InfiniteData } from '@tanstack/react-query';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { NORMAL_INTERVAL } from '../../../../core/jobs/hooks/utils';
import { JobType } from '../../../../core/jobs/jobs.const';
import { JobsResponse } from '../../../../core/jobs/services/jobs-service.interface';
import { FUX_NOTIFICATION_KEYS, FUX_SETTINGS_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../../core/user-settings/hooks/use-global-settings.hook';
import { useFuxNotifications } from '../../../../hooks/use-fux-notifications/use-fux-notifications.hook';
import { useIsAutoTrainingOn } from '../../../../pages/annotator/hooks/use-is-auto-training-on.hook';
import { onFirstScheduledAutoTrainingJob } from '../../../../pages/annotator/notification/auto-training-credits-modal/util';
import { useProject } from '../../../../pages/project-details/providers/project-provider/project-provider.component';
import { getFuxSetting } from '../../tutorials/utils';
import { CoachMark } from '../coach-mark.component';

const useAutoTrainingCoachMarkJobs = () => {
    const { project, projectIdentifier } = useProject();
    const settings = useUserGlobalSettings();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();
    const { handleFirstAutoTraining } = useFuxNotifications();
    const { useGetJobs } = useJobs(projectIdentifier);

    const isAutoTrainingOn = useIsAutoTrainingOn({ project, projectIdentifier });
    const neverAutoTrained = getFuxSetting(FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED, settings.config);
    const isQueryEnabled = Boolean(!FEATURE_FLAG_CREDIT_SYSTEM && isAutoTrainingOn && neverAutoTrained);

    const handleSuccess = useCallback(
        (jobs: InfiniteData<JobsResponse>) =>
            onFirstScheduledAutoTrainingJob(settings, (jobId: string) => {
                if (isQueryEnabled) {
                    handleFirstAutoTraining(project.id, jobId);
                }
            })(jobs),
        [isQueryEnabled, project.id, handleFirstAutoTraining, settings]
    );

    const jobsQuery = useGetJobs(
        { jobTypes: [JobType.TRAIN], projectId: projectIdentifier.projectId },
        {
            enabled: isQueryEnabled,
            refetchInterval: NORMAL_INTERVAL,
        }
    );

    useEffect(() => {
        if (!isQueryEnabled || !jobsQuery.isSuccess) {
            return;
        }

        handleSuccess(jobsQuery.data);
    }, [isQueryEnabled, jobsQuery.isSuccess, jobsQuery.data, handleSuccess]);
};

export const AutoTrainingCoachMark = ({ styles = {} }: { styles?: CSSProperties }) => {
    useAutoTrainingCoachMarkJobs();

    return (
        <CoachMark
            settingsKey={FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED}
            styles={{
                position: 'absolute',
                zIndex: 99999,
                right: '26px',
                top: '50px',
                maxWidth: '894px',
                ...styles,
            }}
        />
    );
};
