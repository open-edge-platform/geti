// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { useQueryClient } from '@tanstack/react-query';

import { useGetRunningJobs } from '../../../../../core/jobs/hooks/use-jobs.hook';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';

export const useIsTraining = (): boolean => {
    const projectIdentifier = useProjectIdentifier();
    const client = useQueryClient();

    const { data } = useGetRunningJobs({ projectId: projectIdentifier.projectId });

    const isTraining = (data?.pages[0]?.jobsCount?.numberOfRunningJobs ?? 0) >= 1;
    const prevIsTrainingValue = useRef<boolean>(false);

    useEffect(() => {
        if (prevIsTrainingValue.current && !isTraining) {
            Promise.all([
                // TODO: revisit these 2 invalidations. Maybe leverage refetchInterval instead.
                client.invalidateQueries({ queryKey: QUERY_KEYS.MODELS_KEY(projectIdentifier) }),
                client.invalidateQueries({ queryKey: QUERY_KEYS.PROJECT_KEY(projectIdentifier) }),
            ]).then();
        }

        prevIsTrainingValue.current = isTraining;
    }, [client, isTraining, projectIdentifier]);

    return isTraining;
};
