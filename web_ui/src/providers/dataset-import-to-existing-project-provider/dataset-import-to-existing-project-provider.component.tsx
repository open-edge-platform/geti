// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, Dispatch, ReactNode, SetStateAction, useContext, useEffect, useMemo, useState } from 'react';

import { useQueryClient } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { DATASET_IMPORT_STATUSES } from '../../core/datasets/dataset.enum';
import { DatasetImportToExistingProjectItem } from '../../core/datasets/dataset.interface';
import { useDatasetImportQueries } from '../../core/datasets/hooks/use-dataset-import-queries.hook';
import { useLocalStorageDatasetImport } from '../../core/datasets/hooks/use-local-storage-dataset-import.hook';
import { ProjectIdentifier } from '../../core/projects/core.interface';
import { CreateDatasetResponse } from '../../core/projects/dataset.interface';
import QUERY_KEYS from '../../core/requests/query-keys';
import { useApplicationServices } from '../../core/services/application-services-provider.component';
import { PinnedCollapsedItemsAction } from '../../hooks/use-pinned-collapsed-items/use-pinned-collapsed-items.interface';
import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../notification/notification.component';
import { useDatasetIdentifier } from '../../pages/annotator/hooks/use-dataset-identifier.hook';
import { useMedia } from '../../pages/media/providers/media-provider.component';
import { useProject } from '../../pages/project-details/providers/project-provider/project-provider.component';
import { LOCAL_STORAGE_KEYS } from '../../shared/local-storage-keys';
import { MissingProviderError } from '../../shared/missing-provider-error';
import { getFileSize, runWhenTruthy } from '../../shared/utils';
import { idMatchingFormat } from '../../test-utils/id-utils';
import { getBytesRemaining, getTimeRemaining } from '../dataset-import-to-new-project-provider/utils';
import { useDataset } from '../dataset-provider/dataset-provider.component';
import { useTusUpload } from '../tus-upload-provider/tus-upload-provider.component';
import { getUploadId, onErrorMessage, throttleProgress } from '../tus-upload-provider/util';
import { useWorkspaceIdentifier } from '../workspaces-provider/use-workspace-identifier.hook';
import { getDatasetImportInitialState, getLabelsMap, matchStatus } from './utils';

interface DatasetImportToExistingProjectContextProps {
    isReady: (id: string | undefined) => boolean;

    setActiveDatasetImportId: Dispatch<SetStateAction<string | undefined>>;

    activeDatasetImport: DatasetImportToExistingProjectItem | undefined;

    patchActiveDatasetImport: (item: Partial<DatasetImportToExistingProjectItem>) => void;
    deleteActiveDatasetImport: () => void;

    prepareDataset: (file: File, selectedDatasetId?: string) => string | undefined;
    prepareDatasetAction: (id: string, uploadId: string | null) => void;
    prepareDatasetActionJob: (id: string, uploadId: string | null) => void;

    importDataset: (id: string) => void;
    importDatasetJob: (id: string) => void;

    abortDatasetImportAction: (uploadId: string | null) => void;

    datasetImports: DatasetImportToExistingProjectItem[];

    patchDatasetImport: (partialItem: Partial<DatasetImportToExistingProjectItem>) => void;
    deleteDatasetImport: (id: string | undefined) => void;
}
const DatasetImportToExistingProjectContext = createContext<DatasetImportToExistingProjectContextProps | undefined>(
    undefined
);

interface DatasetImportToExistingProjectProviderProps {
    children: ReactNode;
}

const getDatasetImportToExistingProjectKey = ({ organizationId, workspaceId, projectId }: ProjectIdentifier) => {
    return `${LOCAL_STORAGE_KEYS.IMPORT_DATASET_TO_EXISTING_PROJECT}-${organizationId}-${workspaceId}-${projectId}`;
};

export const DatasetImportToExistingProjectProvider = ({ children }: DatasetImportToExistingProjectProviderProps) => {
    const client = useQueryClient();
    const { loadNextMedia } = useMedia();
    const { router } = useApplicationServices();
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { project, projectIdentifier } = useProject();
    const { addNotification } = useNotification();
    const { setActiveUpload, uploadFile } = useTusUpload();
    const { selectedDataset, handleSelectDataset, dispatchDatasetsTabs } = useDataset();

    const {
        prepareDatasetToExistingProject,
        prepareDatasetToExistingProjectJob,
        importDatasetToExistingProject,
        importDatasetToExistingProjectJob,
        deleteImportProjectFromDataset,
    } = useDatasetImportQueries();

    const {
        lsDatasetImports,

        setLsDatasetImports,

        getLsDatasetImport,
        putLsDatasetImport,
        patchLsDatasetImport,
        deleteLsDatasetImport,
    } = useLocalStorageDatasetImport<DatasetImportToExistingProjectItem>(
        getDatasetImportToExistingProjectKey(projectIdentifier)
    );

    const { datasetId } = useDatasetIdentifier();

    const [activeDatasetImportId, setActiveDatasetImportId] = useState<string>();
    const [abortControllers, setAbortControllers] = useState<Map<string, AbortController>>(new Map());

    const activeDatasetImport = useMemo<DatasetImportToExistingProjectItem | undefined>(() => {
        return getLsDatasetImport(activeDatasetImportId);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeDatasetImportId, lsDatasetImports]);

    const datasetImports = useMemo<DatasetImportToExistingProjectItem[] | []>(() => {
        return (
            lsDatasetImports?.filter(
                (item: DatasetImportToExistingProjectItem) => item.datasetId === selectedDataset.id
            ) ?? []
        );
    }, [lsDatasetImports, selectedDataset]);

    const setAbortController = (uploadId: string, abortController: AbortController): void => {
        abortControllers.set(uploadId, abortController);
        setAbortControllers(new Map(abortControllers));
    };

    const patchActiveDatasetImport = (partialItem: Partial<DatasetImportToExistingProjectItem>): void => {
        if (!activeDatasetImport) return;

        patchLsDatasetImport({ ...activeDatasetImport, ...partialItem });
    };

    const deleteActiveDatasetImport = (): void => {
        if (!activeDatasetImport) return;

        deleteImportProjectFromDataset.mutate(
            { workspaceId, organizationId, fileId: String(activeDatasetImport.uploadId) },
            {
                onSuccess: () => deleteLsDatasetImport(activeDatasetImport.id),
            }
        );
    };

    const isReady = (id: string | undefined): boolean => {
        const datasetImportItem = getLsDatasetImport(id);
        return (
            matchStatus(datasetImportItem, [
                DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
                DATASET_IMPORT_STATUSES.READY,
            ]) && !isEmpty(datasetImportItem?.uploadId)
        );
    };

    const prepareDataset = (file: File, selectedDatasetId?: string): string | undefined => {
        const currentDatasetId = selectedDatasetId ?? datasetId ?? '';
        const { name: fileName, type: fileType, size: fileSize, lastModified: fileLastModified } = file;
        const id = `${idMatchingFormat(fileName)}-${currentDatasetId}-${fileType}-${fileSize}-${fileLastModified}`;

        const datasetImportInitialState = getDatasetImportInitialState({
            id,
            name: fileName,
            size: getFileSize(fileSize),
            projectId: projectIdentifier.projectId,
            datasetId: currentDatasetId,
        });

        putLsDatasetImport(datasetImportInitialState);
        const onThrottleProgress = throttleProgress(() => getLsDatasetImport(id));

        const upload = uploadFile({
            file,
            endpoint: router.DATASET.IMPORT_TUS(projectIdentifier),
            onError: onErrorMessage((message: string): void => {
                patchLsDatasetImport({ id, progress: 0, status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR });
                addNotification({ message, type: NOTIFICATION_TYPE.ERROR });
            }),
            onProgress: onThrottleProgress((datasetImportItem, bytesSent, bytesTotal): void => {
                const { startFromBytes, startAt } = datasetImportItem;
                const uploadId = getUploadId(upload.url);

                patchLsDatasetImport({
                    id,
                    uploadId,
                    progress: Math.floor((bytesSent / bytesTotal) * 100),
                    startFromBytes: startFromBytes > 0 ? startFromBytes : bytesSent,
                    bytesRemaining: getBytesRemaining(bytesTotal - bytesSent),
                    timeRemaining: getTimeRemaining(startAt, bytesSent - startFromBytes, bytesTotal - bytesSent),
                });
            }),
            onSuccess: (): void => {
                const uploadId = getUploadId(upload.url);

                prepareDatasetActionJob(id, uploadId);
            },
        });

        setActiveUpload(id, upload);

        return id;
    };

    const prepareDatasetActionJob = (id: string, uploadId: string | null): void => {
        if (!uploadId) {
            patchLsDatasetImport({
                id,
                progress: 0,
                status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR,
            });
            addNotification({ message: `Upload ${uploadId} not found`, type: NOTIFICATION_TYPE.ERROR });
            return;
        }

        patchLsDatasetImport({
            id,
            uploadId,
            progress: 100,
            timeRemaining: null,
            status: DATASET_IMPORT_STATUSES.PREPARING,
        });

        // Note: we use `mutateAsync` here because it runs the event EVEN after the component has been unmounted.
        prepareDatasetToExistingProjectJob
            .mutateAsync({ ...projectIdentifier, uploadId, setAbortController })
            .then(({ jobId }) => {
                patchLsDatasetImport({ id, preparingJobId: jobId });
            })
            .catch((error) => {
                patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.PREPARING_ERROR });
                addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
            });
    };

    const prepareDatasetAction = (id: string, uploadId: string | null): void => {
        if (!uploadId) {
            patchLsDatasetImport({
                id,
                progress: 0,
                status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR,
            });
            addNotification({ message: `Upload ${uploadId} not found`, type: NOTIFICATION_TYPE.ERROR });
            return;
        }

        patchLsDatasetImport({
            id,
            uploadId,
            progress: 100,
            timeRemaining: null,
            status: DATASET_IMPORT_STATUSES.PREPARING,
        });

        prepareDatasetToExistingProject.mutate(
            { ...projectIdentifier, uploadId, setAbortController },
            {
                onSuccess: ({ warnings, labels }) => {
                    patchLsDatasetImport({
                        id,
                        labels,
                        warnings,
                        uploadId,
                        labelsMap: getLabelsMap(labels, project.labels),
                        status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
                    });
                },
                onError: (error) => {
                    patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.PREPARING_ERROR });
                    addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
                },
            }
        );
    };

    const importDataset = (id: string): void => {
        const datasetImportItem = getLsDatasetImport(id);
        const hasImportFromDatasetRequest =
            datasetImportItem?.status === DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT;

        if (hasImportFromDatasetRequest) {
            return;
        }

        if (!datasetImportItem) {
            deleteLsDatasetImport(id);
            return;
        }

        const { uploadId, datasetId: importItemDatasetId, datasetName, labelsMap } = datasetImportItem;

        if (!uploadId) {
            patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR });
            addNotification({ message: `Upload ${uploadId} not found`, type: NOTIFICATION_TYPE.ERROR });
            return;
        }

        patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT });

        importDatasetToExistingProject.mutate(
            {
                ...projectIdentifier,
                uploadId,
                datasetId: importItemDatasetId,
                datasetName,
                labelsMap,
                setAbortController,
            },
            {
                onSuccess: async (dataset: CreateDatasetResponse) => {
                    deleteLsDatasetImport(id);

                    if (!isEmpty(importItemDatasetId)) {
                        loadNextMedia(true);
                    } else {
                        await client.invalidateQueries({ queryKey: QUERY_KEYS.PROJECT_KEY(projectIdentifier) });

                        dispatchDatasetsTabs({ type: PinnedCollapsedItemsAction.CREATE, payload: dataset });
                        handleSelectDataset(dataset.id);
                    }

                    await client.invalidateQueries({
                        queryKey: QUERY_KEYS.ADVANCED_MEDIA_ITEMS(
                            {
                                ...projectIdentifier,
                                datasetId: selectedDataset.id,
                            },
                            {},
                            {}
                        ),
                    });
                },
                onError: (error) => {
                    patchLsDatasetImport({
                        id,
                        status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR,
                    });

                    addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
                },
            }
        );
    };

    const importDatasetJob = (id: string): void => {
        const datasetImportItem = getLsDatasetImport(id);
        const hasImportFromDatasetRequest =
            datasetImportItem?.status === DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT;

        if (hasImportFromDatasetRequest) {
            return;
        }

        if (!datasetImportItem) {
            deleteLsDatasetImport(id);
            return;
        }

        const { uploadId, datasetId: importItemDatasetId, datasetName, labelsMap } = datasetImportItem;

        if (!uploadId) {
            patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR });
            addNotification({ message: `Upload ${uploadId} not found`, type: NOTIFICATION_TYPE.ERROR });
            return;
        }

        patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT });

        importDatasetToExistingProjectJob.mutate(
            {
                ...projectIdentifier,
                uploadId,
                datasetId: importItemDatasetId,
                datasetName,
                labelsMap: isEmpty(labelsMap) ? {} : labelsMap,
                setAbortController,
            },
            {
                onSuccess: ({ jobId }) => {
                    patchLsDatasetImport({ id, importingJobId: jobId });
                },
                onError: (error) => {
                    patchLsDatasetImport({
                        id,
                        status: DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT_ERROR,
                    });

                    addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
                },
            }
        );
    };

    const abortDatasetImportAction = runWhenTruthy((uploadId: string) => {
        abortControllers.get(uploadId)?.abort();
        abortControllers.delete(uploadId) && setAbortControllers(new Map(abortControllers));
    });

    /*
        Invert READY and LABELS_MAPPING_TO_EXISTING_PROJECT statuses for different isReady
        event states for correct rendering of components and status related messages
    */
    useEffect(() => {
        if (
            !activeDatasetImport ||
            matchStatus(activeDatasetImport, DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT)
        ) {
            return;
        }

        if (
            isReady(activeDatasetImport.id) &&
            matchStatus(activeDatasetImport, DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT)
        ) {
            patchActiveDatasetImport({
                status: DATASET_IMPORT_STATUSES.READY,
            });
        }

        if (!isReady(activeDatasetImport.id) && matchStatus(activeDatasetImport, DATASET_IMPORT_STATUSES.READY)) {
            patchActiveDatasetImport({
                status: DATASET_IMPORT_STATUSES.LABELS_MAPPING_TO_EXISTING_PROJECT,
            });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeDatasetImport]);

    useEffect(() => {
        const storedDatasetImports = lsDatasetImports ?? [];

        setLsDatasetImports(storedDatasetImports);
        for (const storedDatasetImport of storedDatasetImports) {
            const { id, status } = storedDatasetImport;

            switch (status) {
                case DATASET_IMPORT_STATUSES.UPLOADING:
                    if (getLsDatasetImport(id) !== undefined) return;

                    patchLsDatasetImport({
                        ...storedDatasetImport,
                        status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED,
                    });

                    break;
                case DATASET_IMPORT_STATUSES.IMPORTING_TO_EXISTING_PROJECT:
                    importDatasetJob(id);
                    break;
            }
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <DatasetImportToExistingProjectContext.Provider
            value={{
                isReady,

                setActiveDatasetImportId,

                activeDatasetImport,

                patchActiveDatasetImport,
                deleteActiveDatasetImport,

                prepareDataset,
                prepareDatasetAction,
                prepareDatasetActionJob,

                importDataset,
                importDatasetJob,

                abortDatasetImportAction,

                datasetImports,
                patchDatasetImport: patchLsDatasetImport,
                deleteDatasetImport: deleteLsDatasetImport,
            }}
        >
            {children}
        </DatasetImportToExistingProjectContext.Provider>
    );
};

export const useDatasetImportToExistingProject = (): DatasetImportToExistingProjectContextProps => {
    const context = useContext(DatasetImportToExistingProjectContext);

    if (context === undefined) {
        throw new MissingProviderError('useDatasetImportToExistingProject', 'DatasetImportToExistingProjectProvider');
    }

    return context;
};
