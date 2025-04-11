// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { ProjectIdentifier } from '../core.interface';
import { ProjectStatus } from '../project-status.interface';

export const useProjectStatus = (projectIdentifier: ProjectIdentifier): UseQueryResult<ProjectStatus, AxiosError> => {
    const service = useApplicationServices().projectService;

    return useQuery<ProjectStatus, AxiosError>({
        queryKey: QUERY_KEYS.PROJECT_STATUS_KEY(projectIdentifier),
        queryFn: () => {
            return service.getProjectStatus(projectIdentifier);
        },
        notifyOnChangeProps: ['data'],
        meta: { notifyOnError: true },
        refetchInterval: (query) => {
            return query?.state.data?.isTraining ? 10_000 : false;
        },
    });
};
