// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedMaintenanceInfo } from '../../../test-utils/mocked-items-factory/mocked-maintenance';
import { MaintenanceResponse, MaintenanceService } from './maintenance.interface';

export const createInMemoryApiMaintenanceService = (): MaintenanceService => {
    const getMaintenanceInfo = async (): Promise<MaintenanceResponse> => Promise.resolve(getMockedMaintenanceInfo());

    return { getMaintenanceInfo };
};
