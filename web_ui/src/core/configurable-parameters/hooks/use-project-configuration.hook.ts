// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { queryOptions, useQuery } from '@tanstack/react-query';

import { ProjectIdentifier } from '../../projects/core.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { CreateApiModelConfigParametersService } from '../services/api-model-config-parameters-service';

const projectConfigurationQueryOptions = (
    service: CreateApiModelConfigParametersService,
    projectIdentifier: ProjectIdentifier
) =>
    queryOptions({
        queryKey: QUERY_KEYS.CONFIGURATION_PARAMETERS.PROJECT(projectIdentifier),
        queryFn: () => {
            return service.getProjectConfiguration(projectIdentifier);
        },
    });

export const useProjectConfigurationQuery = (projectIdentifier: ProjectIdentifier) => {
    const { configParametersService } = useApplicationServices();

    return useQuery(projectConfigurationQueryOptions(configParametersService, projectIdentifier));
};
