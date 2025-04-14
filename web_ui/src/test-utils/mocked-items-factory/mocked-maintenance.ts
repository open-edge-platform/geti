// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MaintenanceResponse } from '../../core/maintenance/services/maintenance.interface';

export const getMockedMaintenanceInfo = (maintenanceInfo: Partial<MaintenanceResponse> = {}) => {
    return {
        maintenance: {
            enabled: true,
            window: {
                start: 1711312113376,
                end: 1711513116880,
            },
        },
        ...maintenanceInfo,
    };
};
