// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';
import { isAxiosError } from 'axios';
import { StatusCodes } from 'http-status-codes';

import { CreateApiService } from '../../../../packages/core/src/services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { GlobalStatusDTO } from '../dtos/status.interface';
import { StatusProps } from '../status.interface';
import { getGlobalStatus } from '../utils';
import { StatusService } from './status-service.interface';

export const createApiStatusService: CreateApiService<StatusService> = (
    { instance, router } = { instance: apiClient, router: API_URLS }
) => {
    const getStatus = async (organizationId?: string): Promise<StatusProps> => {
        const url = router.STATUS(organizationId);

        try {
            const { data } = await instance.get<GlobalStatusDTO>(url);

            return getGlobalStatus(data);
        } catch (error) {
            if (isAxiosError(error) && error.response?.status === StatusCodes.FORBIDDEN) {
                return {
                    freeSpace: 0,
                    totalSpace: 0,
                    runningJobs: 0,
                };
            }

            throw error;
        }
    };

    return { getStatus };
};
