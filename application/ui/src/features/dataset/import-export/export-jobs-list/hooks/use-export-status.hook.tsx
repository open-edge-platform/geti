// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from 'react';

import { $api } from '@/api';
import type { ExportDatasetJob } from '@/api/types';
import { useStreamJobDetail } from 'hooks/api/jobs/jobs.hook';
import { isInvalidJob } from 'hooks/api/util';

import { useExportDataset } from '../../../../../hooks/storage/use-export-dataset.hook';

export const useExportStatus = (jobId: string) => {
    const { removeLsExportId } = useExportDataset();

    useStreamJobDetail(jobId);

    const response = $api.useQuery(
        'get',
        '/api/jobs/{job_id}',
        { params: { path: { job_id: jobId } } },
        {
            select: (currentData) => currentData as ExportDatasetJob,
        }
    );

    useEffect(() => {
        if (response.isError && isInvalidJob(response.error)) {
            removeLsExportId(jobId);
        }
    }, [jobId, removeLsExportId, response.error, response.isError]);

    return response;
};
