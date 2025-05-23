// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import QUERY_KEYS from '../../../../packages/core/src/requests/query-keys';
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
