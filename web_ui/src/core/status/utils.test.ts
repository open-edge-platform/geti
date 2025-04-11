// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
