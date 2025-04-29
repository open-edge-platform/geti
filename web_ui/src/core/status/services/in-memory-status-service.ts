// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { StatusProps } from '../status.interface';
import { StatusService } from './status-service.interface';

export const createInMemoryStatusService = (): StatusService => {
    const getStatus = async (_organizationId?: string): Promise<StatusProps> => {
        return Promise.resolve({ runningJobs: 1, freeSpace: 85000000000, totalSpace: 100000000000 });
    };

    return { getStatus };
};
