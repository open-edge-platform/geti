// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useImportJobStatus } from 'hooks/api/jobs/use-import-job-status.hook';
import { isJobFailed, isJobPending, isJobRunning } from 'hooks/api/util';
import { useTranslation } from 'react-i18next';

import { ImportActiveJob } from '../import-card-status/import-active-job/import-active-job.component';
import { ImportFailedJob } from '../import-card-status/import-failed-job/import-failed-job.component';

type PrepareImportDatasetProps = {
    size: number;
    jobId: string;
    fileName: string;
    stagedDatasetId: string;
    onSuccess: () => void;
    deleteEntry: () => void;
};

export const PrepareImportDataset = ({
    size,
    jobId,
    fileName,
    stagedDatasetId,
    onSuccess,
    deleteEntry,
}: PrepareImportDatasetProps) => {
    const { t } = useTranslation();

    const { data: job, isError, error } = useImportJobStatus({ jobId, onSuccess });

    const isRunningOrPending = job !== undefined && (isJobRunning(job) || isJobPending(job));

    return (
        <>
            {isJobFailed(job) && (
                <ImportFailedJob
                    size={size}
                    fileName={fileName}
                    error={job?.error ?? ''}
                    message={job?.message ?? ''}
                    stagedDatasetId={stagedDatasetId}
                    deleteEntry={deleteEntry}
                />
            )}

            {isError && (
                <ImportFailedJob
                    size={size}
                    fileName={fileName}
                    error={`${error?.detail ?? t('common.unknownError')}`}
                    message={t('common.importPreparationError')}
                    stagedDatasetId={stagedDatasetId}
                    deleteEntry={deleteEntry}
                />
            )}

            {isRunningOrPending && (
                <ImportActiveJob
                    job={job}
                    size={size}
                    fileName={fileName}
                    stagedDatasetId={stagedDatasetId}
                    deleteEntry={deleteEntry}
                />
            )}
        </>
    );
};
