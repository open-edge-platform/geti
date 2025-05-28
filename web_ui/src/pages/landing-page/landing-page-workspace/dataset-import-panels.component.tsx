// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Fragment } from 'react';

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { View } from '@geti/ui';
import { OverlayTriggerState, useOverlayTriggerState } from '@react-stately/overlays';
import { useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { isEmpty } from 'lodash-es';

import { DATASET_IMPORT_STATUSES } from '../../../core/datasets/dataset.enum';
import { DatasetImportItem, DatasetImportToNewProjectItem } from '../../../core/datasets/dataset.interface';
import { useDatasetImportQueries } from '../../../core/datasets/hooks/use-dataset-import-queries.hook';
import { getCurrentJob, isImportingNewProjectJob, isPreparingJob } from '../../../core/datasets/utils';
import { useJobs } from '../../../core/jobs/hooks/use-jobs.hook';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { useDatasetImportToNewProject } from '../../../providers/dataset-import-to-new-project-provider/dataset-import-to-new-project-provider.component';
import { formatDatasetPrepareImportResponse } from '../../../providers/dataset-import-to-new-project-provider/utils';
import { useWorkspaceIdentifier } from '../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { DatasetImportPanel } from '../../../shared/components/dataset-import-panel/dataset-import-panel.component';
import { isNonEmptyString } from '../../../shared/utils';
import { DatasetImportToNewProjectDialog } from './components/dataset-import-to-new-project/dataset-import-to-new-project-dialog.component';

import classes from './landing-page-workspace.module.scss';

interface DatasetImportPanelsProps {
    areProjectsLoading: boolean;
    datasetImportDialogTrigger: OverlayTriggerState;
}

interface DatasetImportJobStatusProps {
    workspaceId: string;
    organizationId: string;
    datasetImportItem: DatasetImportItem;
    deleteDatasetImport: (id: string) => void;
    patchDatasetImport: (partialItem: Partial<DatasetImportToNewProjectItem>) => void;
}

const DatasetImportJobStatus = ({
    workspaceId,
    organizationId,
    datasetImportItem,
    patchDatasetImport,
    deleteDatasetImport,
}: DatasetImportJobStatusProps) => {
    const client = useQueryClient();
    const { addNotification } = useNotification();
    const { usePreparingStatusJob, useImportingStatusJob } = useDatasetImportQueries();

    const { id, uploadId, preparingJobId, importingJobId } = datasetImportItem;

    usePreparingStatusJob({
        data: { organizationId, workspaceId, jobId: String(preparingJobId) },
        enabled: isPreparingJob(datasetImportItem),
        onSuccess: (jobResponse) => {
            patchDatasetImport(
                formatDatasetPrepareImportResponse({
                    id,
                    uploadId: String(uploadId),
                    warnings: jobResponse.metadata.warnings ?? [],
                    supportedProjectTypes: jobResponse.metadata.supportedProjectTypes ?? [],
                })
            );
        },
        onError: (error: AxiosError) => {
            patchDatasetImport({ id, status: DATASET_IMPORT_STATUSES.PREPARING_ERROR });
            addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
        },
        onCancel: () => {
            deleteDatasetImport(datasetImportItem.id);
        },
        onSettled: () => {
            patchDatasetImport({ id, preparingJobId: null });
        },
    });

    useImportingStatusJob({
        data: { organizationId, workspaceId, jobId: String(importingJobId) },
        enabled: isImportingNewProjectJob(datasetImportItem),
        onSuccess: async () => {
            deleteDatasetImport(datasetImportItem.id);

            await client.invalidateQueries({ queryKey: QUERY_KEYS.PROJECTS_KEY(workspaceId) });
        },
        onError: (error: AxiosError) => {
            patchDatasetImport({ id, status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR });
            addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
        },
        onCancel: () => {
            deleteDatasetImport(datasetImportItem.id);
        },
    });

    return <></>;
};

export const DatasetImportPanels = ({
    areProjectsLoading,
    datasetImportDialogTrigger,
}: DatasetImportPanelsProps): JSX.Element => {
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { useCancelJob } = useJobs({ organizationId, workspaceId });
    const datasetImportDeletionDialogTrigger = useOverlayTriggerState({});

    const {
        isReady,
        isDeleting,
        datasetImports,
        prepareDataset,
        importDatasetJob,
        patchDatasetImport,
        deleteDatasetImport,
        prepareDatasetActionJob,
        setActiveDatasetImportId,
        deleteTemporallyDatasetImport,
    } = useDatasetImportToNewProject();

    const abortDatasetImportActionHandler = (datasetImportItem: DatasetImportItem) => {
        const currentJobId = getCurrentJob(datasetImportItem);

        isNonEmptyString(currentJobId) && useCancelJob.mutate(currentJobId);
    };

    return (
        <>
            {!isEmpty(datasetImports) ? (
                <View position={'relative'} UNSAFE_className={classes.datasetImportPanels}>
                    {!areProjectsLoading &&
                        datasetImports
                            .sort((a, b) => b.startAt - a.startAt)
                            .map((datasetImportItem: DatasetImportItem) => (
                                <Fragment key={datasetImportItem.id}>
                                    <DatasetImportJobStatus
                                        workspaceId={workspaceId}
                                        organizationId={organizationId}
                                        datasetImportItem={datasetImportItem}
                                        patchDatasetImport={patchDatasetImport}
                                        deleteDatasetImport={deleteDatasetImport}
                                    />
                                    <DatasetImportPanel
                                        isReady={isReady}
                                        isDeleting={isDeleting}
                                        primaryActionName={'Create'}
                                        prepareDataset={prepareDataset}
                                        datasetImportItem={datasetImportItem}
                                        prepareDatasetAction={prepareDatasetActionJob}
                                        datasetImportDialogTrigger={datasetImportDialogTrigger}
                                        datasetImportDeleteDialogTrigger={datasetImportDeletionDialogTrigger}
                                        onPrimaryAction={() => {
                                            importDatasetJob(datasetImportItem.id);
                                        }}
                                        setActiveDatasetImportId={setActiveDatasetImportId}
                                        abortDatasetImportAction={() =>
                                            abortDatasetImportActionHandler(datasetImportItem)
                                        }
                                        onDeleteAction={() => deleteTemporallyDatasetImport(datasetImportItem)}
                                    />
                                </Fragment>
                            ))}
                </View>
            ) : null}

            <DatasetImportToNewProjectDialog
                trigger={datasetImportDialogTrigger}
                deleteDialogTrigger={datasetImportDeletionDialogTrigger}
            />
        </>
    );
};
