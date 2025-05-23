// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { View } from '@geti/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { DATASET_IMPORT_STATUSES } from '../../../../core/datasets/dataset.enum';
import { DatasetImportItem, DatasetImportToExistingProjectItem } from '../../../../core/datasets/dataset.interface';
import { getCurrentJob, isImportingExistingProjectJob, isPreparingJob } from '../../../../core/datasets/utils';
import { useJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { ProjectProps } from '../../../../core/projects/project.interface';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { useProject } from '../../../../pages/project-details/providers/project-provider/project-provider.component';
import { useWorkspaceIdentifier } from '../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { isNonEmptyArray, isNonEmptyString } from '../../../../shared/utils';
import { useExportImportDatasetDialogStates } from '../../../dataset-export/components/export-import-dataset-dialog-provider.component';
import { useDatasetImportQueries } from '../../hooks/use-dataset-import-queries.hook';
import { useDatasetImportToExistingProject } from '../../providers/dataset-import-to-existing-project-provider/dataset-import-to-existing-project-provider.component';
import { getLabelsMap } from '../../providers/dataset-import-to-existing-project-provider/utils';
import { DatasetImportDeletionDialog } from '../dataset-import-deletion-dialog/dataset-import-deletion-dialog.component';
import { DatasetImportPanel } from '../dataset-import-panel/dataset-import-panel.component';
import { DatasetImportToExistingProjectDialog } from './dataset-import-to-existing-project-dialog.component';

interface DatasetImportJobStatusProps {
    project: ProjectProps;
    datasetImportItem: DatasetImportItem;
    deleteDatasetImport: (id: string) => void;
    patchDatasetImport: (partialItem: Partial<DatasetImportToExistingProjectItem>) => void;
}

const DatasetImportJobStatus = ({
    project,
    datasetImportItem,
    patchDatasetImport,
    deleteDatasetImport,
}: DatasetImportJobStatusProps) => {
    const client = useQueryClient();
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { addNotification } = useNotification();
    const { usePreparingExistingProjectStatusJob, useImportingExistingProjectStatusJob } = useDatasetImportQueries();

    const { id, uploadId, preparingJobId, importingJobId } = datasetImportItem;

    usePreparingExistingProjectStatusJob({
        data: { organizationId, workspaceId, jobId: String(preparingJobId) },
        enabled: isPreparingJob(datasetImportItem),
        onSuccess: ({ metadata }) => {
            patchDatasetImport({
                id,
                uploadId,
                labels: metadata.labels,
                warnings: metadata.warnings,
                labelsMap: isNonEmptyArray(metadata.labels) ? getLabelsMap(metadata.labels, project.labels) : undefined,
                status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
            });
        },
        onError: (error: AxiosError) => {
            patchDatasetImport({ id, status: DATASET_IMPORT_STATUSES.PREPARING_ERROR });
            addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
        },
        onCancel: () => {
            deleteDatasetImport(datasetImportItem.id);
        },
        onSettled: () => patchDatasetImport({ id, preparingJobId: null }),
    });

    useImportingExistingProjectStatusJob({
        data: { organizationId, workspaceId, jobId: String(importingJobId) },
        enabled: isImportingExistingProjectJob(datasetImportItem),
        onSuccess: async ({ metadata }) => {
            deleteDatasetImport(id);

            await client.invalidateQueries({
                queryKey: QUERY_KEYS.ADVANCED_MEDIA_ITEMS(
                    {
                        organizationId,
                        workspaceId,
                        projectId: project.id,
                        datasetId: String(metadata.dataset?.id),
                    },
                    {},
                    {}
                ),
            });
        },
        onError: (error: AxiosError) => {
            patchDatasetImport({ id, status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR });
            addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
        },
        onCancel: () => {
            deleteDatasetImport(datasetImportItem.id);
        },
    });

    return <></>;
};

export const DatasetImports = () => {
    const { datasetImportDialogState } = useExportImportDatasetDialogStates();
    const datasetImportDeleteDialogState = useOverlayTriggerState({});

    const { project, projectIdentifier } = useProject();
    const { useCancelJob } = useJobs(projectIdentifier);

    const {
        isReady,
        datasetImports,
        importDataset,
        deleteDatasetImport,
        prepareDataset,
        patchDatasetImport,
        prepareDatasetActionJob,
        setActiveDatasetImportId,
        activeDatasetImport,
        deleteActiveDatasetImport,
    } = useDatasetImportToExistingProject();

    const abortDatasetImportActionHandler = (datasetImportItem: DatasetImportItem) => {
        const currentJobId = getCurrentJob(datasetImportItem);

        isNonEmptyString(currentJobId) &&
            useCancelJob.mutateAsync(currentJobId).then(() => deleteDatasetImport(datasetImportItem.id));
    };

    return (
        <>
            {datasetImports.map((datasetImportItem: DatasetImportItem) => (
                <View key={datasetImportItem.id} marginTop='size-250'>
                    <DatasetImportJobStatus
                        project={project}
                        datasetImportItem={datasetImportItem}
                        patchDatasetImport={patchDatasetImport}
                        deleteDatasetImport={deleteDatasetImport}
                    />
                    <DatasetImportPanel
                        isReady={isReady}
                        datasetImportItem={datasetImportItem}
                        datasetImportDialogTrigger={datasetImportDialogState}
                        datasetImportDeleteDialogTrigger={datasetImportDeleteDialogState}
                        onPrimaryAction={() => importDataset(datasetImportItem.id)}
                        onDeleteAction={() => deleteDatasetImport(datasetImportItem.id)}
                        prepareDataset={prepareDataset}
                        prepareDatasetAction={prepareDatasetActionJob}
                        setActiveDatasetImportId={setActiveDatasetImportId}
                        abortDatasetImportAction={() => abortDatasetImportActionHandler(datasetImportItem)}
                    />
                </View>
            ))}

            <DatasetImportToExistingProjectDialog
                datasetImportDialogState={datasetImportDialogState}
                datasetImportDeleteDialogState={datasetImportDeleteDialogState}
            />

            <DatasetImportDeletionDialog
                datasetImportItem={activeDatasetImport}
                trigger={datasetImportDeleteDialogState}
                onPrimaryAction={() => {
                    datasetImportDeleteDialogState.close();
                    datasetImportDialogState.close();
                    deleteActiveDatasetImport();
                }}
            />
        </>
    );
};
