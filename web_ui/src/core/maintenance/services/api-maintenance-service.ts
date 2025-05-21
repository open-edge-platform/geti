// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { client } from '@geti/core';

import { CreateApiService } from '../../services/create-api-service.interface';
import { MaintenanceResponse, MaintenanceService } from './maintenance.interface';

export const createApiMaintenanceService: CreateApiService<MaintenanceService> = () => {
    const getMaintenanceInfo = async (configUrl: string): Promise<MaintenanceResponse> => {
        const { data } = await client.get<MaintenanceResponse>(configUrl);

        return data;
    };

    return { getMaintenanceInfo };
};
