// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useMemo, useRef } from 'react';

import { InfiniteData } from '@tanstack/react-query';

import { useJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { NORMAL_INTERVAL } from '../../../../core/jobs/hooks/utils';
import { JobState, JobType } from '../../../../core/jobs/jobs.const';
import { JobsResponse } from '../../../../core/jobs/services/jobs-service.interface';
import { useModels } from '../../../../core/models/hooks/use-models.hook';
import { ModelPerformance } from '../../../../core/models/models.interface';
import { isAnomalyDomain } from '../../../../core/projects/domains';
import { PerformanceType } from '../../../../core/projects/task.interface';
import { FUX_NOTIFICATION_KEYS, FUX_SETTINGS_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../../core/user-settings/hooks/use-global-settings.hook';
import { useFuxNotifications } from '../../../../hooks/use-fux-notifications/use-fux-notifications.hook';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';
import { useProject } from '../../../../pages/project-details/providers/project-provider/project-provider.component';
import { getFuxSetting } from '../../tutorials/utils';
import { CoachMark } from '../coach-mark.component';
import { onFirstSuccessfulAutoTrainingJob } from '../utils';

const useSuccessfullyAutotrainedNotificationJobs = ({
    enabled,
    onSuccess,
}: {
    enabled: boolean;
    onSuccess: (jobs: InfiniteData<JobsResponse>) => void;
}) => {
    const projectIdentifier = useProjectIdentifier();
    const { useGetJobs } = useJobs(projectIdentifier);
    const handleSuccessRef = useRef(onSuccess);

    const jobsQuery = useGetJobs(
        { jobTypes: [JobType.TRAIN], jobState: JobState.FINISHED, projectId: projectIdentifier.projectId },
        {
            enabled,
            refetchInterval: NORMAL_INTERVAL,
        }
    );

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

export const SuccessfullyAutotrainedNotification = () => {
    const { project } = useProject();
    const settings = useUserGlobalSettings();
    const { handleFirstSuccessfulAutoTraining } = useFuxNotifications();
    const { useProjectModelsQuery } = useModels();
    const { data: modelsData = [] } = useProjectModelsQuery({ refetchInterval: 15000 });
    const isAnomalous = isAnomalyDomain(project.domains[0]);

    const neverSuccessfullyAutoTrained = getFuxSetting(
        FUX_SETTINGS_KEYS.NEVER_SUCCESSFULLY_AUTOTRAINED,
        settings.config
    );
    const firstAutoTrainedModelId = getFuxSetting(FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_MODEL_ID, settings.config);
    const isQueryEnabled = Boolean(neverSuccessfullyAutoTrained);

    const trainedModel = modelsData.find((model) =>
        model.modelVersions.find((modelVersion) => modelVersion.id == firstAutoTrainedModelId)
    );
    const trainedModelVersion = trainedModel
        ? trainedModel.modelVersions.find((modelVersion) => modelVersion.id == firstAutoTrainedModelId)
        : undefined;

    const modelScore = useMemo(() => {
        const performance: ModelPerformance | undefined = trainedModelVersion?.performance;

        if (performance === undefined) {
            return;
        }

        if (performance.type === PerformanceType.DEFAULT) {
            return performance.score;
        }

        return performance.globalScore;
    }, [trainedModelVersion]);

    const customMessage =
        `Your model “${trainedModelVersion?.groupName}” version ${trainedModelVersion?.version} has` +
        ` been successfully trained. Model score is ${modelScore ? Math.round(modelScore * 100) : 0}%.`;

    useSuccessfullyAutotrainedNotificationJobs({
        enabled: isQueryEnabled,
        onSuccess: onFirstSuccessfulAutoTrainingJob(settings, (trainedModelId: string) => {
            if (!isAnomalous && isQueryEnabled && trainedModelId) {
                handleFirstSuccessfulAutoTraining(trainedModelId);
            }
        }),
    });

    if (isAnomalous) {
        return <></>;
    }

    return firstAutoTrainedModelId !== null && trainedModelVersion ? (
        <CoachMark
            settingsKey={FUX_NOTIFICATION_KEYS.ANNOTATOR_SUCCESSFULLY_TRAINED}
            customDescription={customMessage}
            styles={{ position: 'absolute', top: '50px', zIndex: 99999, right: '80px' }}
        />
    ) : (
        <></>
    );
};
