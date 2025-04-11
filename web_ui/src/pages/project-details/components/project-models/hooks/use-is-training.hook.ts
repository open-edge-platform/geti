// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useRef } from 'react';

import { useQueryClient } from '@tanstack/react-query';

import { useGetRunningJobs } from '../../../../../core/jobs/hooks/use-jobs.hook';
import QUERY_KEYS from '../../../../../core/requests/query-keys';
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
