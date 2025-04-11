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

import { isAxiosError } from 'axios';
import { StatusCodes } from 'http-status-codes';

import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { GlobalStatusDTO } from '../dtos/status.interface';
import { StatusProps } from '../status.interface';
import { getGlobalStatus } from '../utils';
import { StatusService } from './status-service.interface';

export const createApiStatusService: CreateApiService<StatusService> = (
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
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
