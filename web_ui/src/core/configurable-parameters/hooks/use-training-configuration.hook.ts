// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { queryOptions, useQuery } from '@tanstack/react-query';

import { ProjectIdentifier } from '../../projects/core.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import {
    CreateApiModelConfigParametersService,
    TrainingConfigurationQueryParameters,
} from '../services/api-model-config-parameters-service';

const trainingConfigurationQueryOptions = (
    service: CreateApiModelConfigParametersService,
    projectIdentifier: ProjectIdentifier,
    queryParameters?: TrainingConfigurationQueryParameters
) =>
    queryOptions({
        queryKey: QUERY_KEYS.CONFIGURATION_PARAMETERS.TRAINING(projectIdentifier, queryParameters),
        queryFn: () => {
            return service.getTrainingConfiguration(projectIdentifier);
        },
    });

export const useTrainingConfigurationQuery = (
    projectIdentifier: ProjectIdentifier,
    queryParameters?: TrainingConfigurationQueryParameters
) => {
    const { configParametersService } = useApplicationServices();

    return useQuery(trainingConfigurationQueryOptions(configParametersService, projectIdentifier, queryParameters));
};
