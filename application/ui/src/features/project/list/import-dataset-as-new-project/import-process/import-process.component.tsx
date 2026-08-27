// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useImportDatasetAsNewProject } from 'hooks/storage/use-import-dataset-as-new-project.hook';
import { useTranslation } from 'react-i18next';

import { ImportJobProcess } from '../../../../../components/import-job-process/import-job-process.component';
import { useImportDatasetDialog } from '../../../providers/import-dataset-dialog-provider.component';

type ImportProcessProps = {
    stagedDatasetId: string;
    onFilePrepared: () => void;
};

export const ImportProcess = ({ stagedDatasetId, onFilePrepared }: ImportProcessProps) => {
    const { t } = useTranslation();
    const { datasetImportDialogState } = useImportDatasetDialog();
    const { getImportEntry, updateImportEntryStep } = useImportDatasetAsNewProject();

    const entry = getImportEntry(stagedDatasetId);

    return (
        <ImportJobProcess
            jobId={entry?.prepareJobId}
            fileName={entry?.fileName ?? ''}
            onError={datasetImportDialogState.close}
            onSuccess={() => {
                onFilePrepared();
                updateImportEntryStep(stagedDatasetId, 'taskTypeSelection');
            }}
            message={t('projectList.import.prepareMessage')}
        />
    );
};
