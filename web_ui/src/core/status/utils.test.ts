// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { GlobalStatusDTO } from './dtos/status.interface';
import { getGlobalStatus } from './utils';

describe('code status utils', () => {
    it('getGlobalStatus', () => {
        expect(
            getGlobalStatus({
                free_space: '',
                n_running_jobs: 1,
                storage: {
                    free_space: 2,
                    total_space: 3,
                },
            })
        ).toEqual({ runningJobs: 1, freeSpace: 2, totalSpace: 3 });

        expect(
            getGlobalStatus({
                free_space: '',
                n_running_jobs: 2,
            } as GlobalStatusDTO)
        ).toEqual({ runningJobs: 2, freeSpace: Infinity, totalSpace: Infinity });
    });
});
