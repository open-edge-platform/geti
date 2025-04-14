// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { GlobalStatusDTO } from './dtos/status.interface';
import { StatusProps } from './status.interface';

export const getGlobalStatus = ({ n_running_jobs, storage }: GlobalStatusDTO): StatusProps => {
    if (!storage) {
        return {
            freeSpace: Infinity,
            totalSpace: Infinity,
            runningJobs: n_running_jobs,
        };
    }

    return {
        freeSpace: storage.free_space,
        totalSpace: storage.total_space,
        runningJobs: n_running_jobs,
    };
};
