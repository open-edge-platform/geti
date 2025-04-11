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

import { DOMAIN } from './core.interface';
import { TASK_TYPE } from './dtos/task.interface';
import { getDomain } from './project.interface';

describe('Project Interface - getDomain', () => {
    it("Check if 'Anomaly' string returns DOMAIN.ANOMALY_CLASSIFICATION", async () => {
        const domain = getDomain(TASK_TYPE.ANOMALY_CLASSIFICATION);
        expect(domain).toBe(DOMAIN.ANOMALY_CLASSIFICATION);
    });

    it("Check if 'Torch segmentation' string returns DOMAIN.SEGMENTATION", async () => {
        const domain = getDomain(TASK_TYPE.SEGMENTATION);
        expect(domain).toBe(DOMAIN.SEGMENTATION);
    });

    it("Check if 'detection' string returns DOMAIN.DETECTION", async () => {
        const domain = getDomain(TASK_TYPE.DETECTION);
        expect(domain).toBe(DOMAIN.DETECTION);
    });

    it('Check if CROP and DATASET return nothing', async () => {
        expect(getDomain(TASK_TYPE.CROP)).toBe(DOMAIN.CROP);
        expect(getDomain(TASK_TYPE.DATASET)).toBe(undefined);
    });
});
