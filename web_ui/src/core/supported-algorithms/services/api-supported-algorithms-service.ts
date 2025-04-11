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

import { ProjectIdentifier } from '../../projects/core.interface';
import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { SupportedAlgorithmsResponseDTO } from '../dtos/supported-algorithms.interface';
import { SupportedAlgorithm } from '../supported-algorithms.interface';
import { SupportedAlgorithmsService } from './supported-algorithms.interface';
import { getSupportedAlgorithmsEntities } from './utils';

export const createApiSupportedAlgorithmsService: CreateApiService<SupportedAlgorithmsService> = (
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
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
