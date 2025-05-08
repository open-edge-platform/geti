// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { JobType } from '../../../../../core/jobs/jobs.const';

export interface FiltersType {
    projectId: string | undefined;
    userId: string | undefined;
    jobTypes: JobType[];
}
