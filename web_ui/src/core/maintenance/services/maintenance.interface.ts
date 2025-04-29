// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface MaintenanceResponse {
    maintenance: {
        enabled: boolean;
        window: {
            start: number;
            end: number;
        };
    };
}

export interface MaintenanceService {
    getMaintenanceInfo: (configUrl: string) => Promise<MaintenanceResponse>;
}
