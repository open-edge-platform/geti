// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { JobInfoStatus } from './dtos/tests.interface';

export const isTestJobCompleted = (status: JobInfoStatus) => {
    return [JobInfoStatus.DONE, JobInfoStatus.ERROR, JobInfoStatus.FAILED].includes(status);
};
