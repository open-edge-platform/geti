// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { instance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { MaintenanceResponse, MaintenanceService } from './maintenance.interface';

export const createApiMaintenanceService: CreateApiService<MaintenanceService> = () => {
    const getMaintenanceInfo = async (configUrl: string): Promise<MaintenanceResponse> => {
        const { data } = await instance.get<MaintenanceResponse>(configUrl);

        return data;
    };

    return { getMaintenanceInfo };
};
