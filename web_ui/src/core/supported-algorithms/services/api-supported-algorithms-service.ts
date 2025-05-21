// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { client } from '@geti/core';

import { ProjectIdentifier } from '../../projects/core.interface';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { SupportedAlgorithmsResponseDTO } from '../dtos/supported-algorithms.interface';
import { SupportedAlgorithm } from '../supported-algorithms.interface';
import { SupportedAlgorithmsService } from './supported-algorithms.interface';
import { getSupportedAlgorithmsEntities } from './utils';

export const createApiSupportedAlgorithmsService: CreateApiService<SupportedAlgorithmsService> = (
    { instance, router } = { instance: client, router: API_URLS }
) => {
    const getProjectSupportedAlgorithms = async (
        projectIdentifier: ProjectIdentifier
    ): Promise<SupportedAlgorithm[]> => {
        const { data } = await instance.get<SupportedAlgorithmsResponseDTO>(
            router.PROJECT_SUPPORTED_ALGORITHMS(projectIdentifier)
        );

        return getSupportedAlgorithmsEntities(data);
    };

    return { getProjectSupportedAlgorithms };
};
