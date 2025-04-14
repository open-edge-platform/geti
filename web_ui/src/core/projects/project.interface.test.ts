// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
