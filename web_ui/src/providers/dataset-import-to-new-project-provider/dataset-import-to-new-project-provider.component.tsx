// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    createContext,
    Dispatch,
    ReactNode,
    SetStateAction,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from 'react';

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { isEmpty, noop } from 'lodash-es';

import { DATASET_IMPORT_STATUSES } from '../../core/datasets/dataset.enum';
import {
    DatasetImportItem,
    DatasetImportLabel,
    DatasetImportToNewProjectItem,
} from '../../core/datasets/dataset.interface';
import { useDatasetImportQueries } from '../../core/datasets/hooks/use-dataset-import-queries.hook';
import { useFeatureFlags } from '../../core/feature-flags/hooks/use-feature-flags.hook';
import { useLocalStorageDatasetImport } from '../../features/dataset-import/hooks/use-local-storage-dataset-import.hook';
import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../notification/notification.component';
import { getRandomDistinctColor } from '../../pages/create-project/components/distinct-colors';
import { getImportDatasetToNewProjectKey } from '../../shared/local-storage-keys';
import { MissingProviderError } from '../../shared/missing-provider-error';
import { getFileSize, isNonEmptyString, runWhenTruthy } from '../../shared/utils';
import { idMatchingFormat } from '../../test-utils/id-utils';
import { matchStatus } from '../dataset-import-to-existing-project-provider/utils';
import { useTusUpload } from '../tus-upload-provider/tus-upload-provider.component';
import { getUploadId, onErrorMessage, throttleProgress } from '../tus-upload-provider/util';
import { useWorkspaceIdentifier } from '../workspaces-provider/use-workspace-identifier.hook';
import {
    formatDatasetPrepareImportResponse,
    getBytesRemaining,
    getDatasetImportInitialState,
    getTimeRemaining,
} from './utils';

interface DatasetImportContextProps {
    isDeleting: boolean;
    isReady: (id: string | undefined) => boolean;

    setActiveDatasetImportId: Dispatch<SetStateAction<string | undefined>>;

    activeDatasetImport: DatasetImportToNewProjectItem | undefined;

    patchActiveDatasetImport: (item: Partial<DatasetImportToNewProjectItem>) => void;
    deleteTemporallyDatasetImport: (datasetImportItem?: DatasetImportItem) => void;

    prepareDataset: (file: File) => string | undefined;

    prepareDatasetAction: (id: string, uploadId: string | null) => void;
    prepareDatasetActionJob: (id: string, uploadId: string | null) => void;

    importDataset: (id: string) => void;
    importDatasetJob: (id: string) => void;

    abortDatasetImportAction: (uploadId: string | null) => void;

    datasetImports: DatasetImportToNewProjectItem[];

    patchDatasetImport: (partialItem: Partial<DatasetImportToNewProjectItem>) => void;
    deleteDatasetImport: (id: string | undefined) => void;
}

const DatasetImportToNewProjectContext = createContext<DatasetImportContextProps | undefined>(undefined);

interface DatasetImportToNewProjectProps {
    children: ReactNode;
}

export const DatasetImportToNewProjectProvider = ({ children }: DatasetImportToNewProjectProps): JSX.Element => {
    const client = useQueryClient();
    const { FEATURE_FLAG_ANOMALY_REDUCTION } = useFeatureFlags();

    const { router } = useApplicationServices();
    const workspaceIdentifier = useWorkspaceIdentifier();
    const { organizationId, workspaceId } = workspaceIdentifier;
    const { addNotification } = useNotification();
    const { setActiveUpload, uploadFile } = useTusUpload();
    const {
        prepareDatasetForNewProject,
        prepareDatasetJob,
        importDatasetToNewProject,
        importDatasetToNewProjectJob,
        deleteImportProjectFromDataset,
    } = useDatasetImportQueries();

    const {
        lsDatasetImports,
        setLsDatasetImports,
        getLsDatasetImport,
        putLsDatasetImport,
        patchLsDatasetImport,
        deleteLsDatasetImport,
    } = useLocalStorageDatasetImport<DatasetImportToNewProjectItem>(
        getImportDatasetToNewProjectKey(workspaceIdentifier)
    );

    const [activeDatasetImportId, setActiveDatasetImportId] = useState<string | undefined>(undefined);
    const [abortControllers, setAbortControllers] = useState<Map<string, AbortController>>(new Map());

    const activeDatasetImport = useMemo<DatasetImportToNewProjectItem | undefined>(() => {
        return getLsDatasetImport(activeDatasetImportId);

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeDatasetImportId, lsDatasetImports]);

    useEffect(() => {
        if (
            !activeDatasetImport ||
            matchStatus(activeDatasetImport, DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT)
        ) {
            return;
        }

        if (
            isReady(activeDatasetImport.id) &&
            matchStatus(activeDatasetImport, DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT)
        ) {
            patchActiveDatasetImport({
                status: DATASET_IMPORT_STATUSES.READY,
            });
        }

        if (!isReady(activeDatasetImport.id) && matchStatus(activeDatasetImport, DATASET_IMPORT_STATUSES.READY)) {
            patchActiveDatasetImport({
                status: DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
            });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeDatasetImport]);

    useEffect(() => {
        const storedDatasetImports = lsDatasetImports ?? [];

        setLsDatasetImports(storedDatasetImports);

        for (const storedDatasetImport of storedDatasetImports) {
            const { id, uploadId, status, preparingJobId } = storedDatasetImport;

            switch (status) {
                case DATASET_IMPORT_STATUSES.UPLOADING:
                    if (getLsDatasetImport(id) !== undefined) return;

                    patchLsDatasetImport({
                        ...storedDatasetImport,
                        status: DATASET_IMPORT_STATUSES.IMPORTING_INTERRUPTED,
                    });
                    break;
                case DATASET_IMPORT_STATUSES.PREPARING:
                    const prepareActionJobOrVoid = isNonEmptyString(preparingJobId) ? noop : prepareDatasetActionJob;
                    prepareActionJobOrVoid(id, uploadId);

                    break;
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const setAbortController = (uploadId: string, abortController: AbortController): void => {
        abortControllers.set(uploadId, abortController);
        setAbortControllers(new Map(abortControllers));
    };

    const patchActiveDatasetImport = useCallback(
        (partialItem: Partial<DatasetImportToNewProjectItem>): void => {
            if (!activeDatasetImport) return;

            patchLsDatasetImport({ ...activeDatasetImport, ...partialItem });
        },
        [activeDatasetImport, patchLsDatasetImport]
    );

    const deleteTemporallyDatasetImport = (datasetImportItem?: DatasetImportItem): void => {
        const datasetImport = datasetImportItem ?? activeDatasetImport;

        if (isEmpty(datasetImport)) return;

        deleteImportProjectFromDataset.mutate(
            { ...workspaceIdentifier, fileId: String(datasetImport.uploadId) },
            {
                onSuccess: () => deleteLsDatasetImport(datasetImport.id),
                onError: (error) => addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR }),
            }
        );
    };

    const deleteDatasetAfterImporting = async (id: string): Promise<void> => {
        deleteLsDatasetImport(id);

        await client.invalidateQueries({ queryKey: QUERY_KEYS.PROJECTS_KEY(workspaceId) });
    };

    const isReady = (id: string | undefined): boolean => {
        const datasetImportItem = getLsDatasetImport(id);

        if (!datasetImportItem) return false;

        const { uploadId, projectName, taskType } = datasetImportItem;

        return (
            matchStatus(datasetImportItem, [
                DATASET_IMPORT_STATUSES.LABELS_SELECTION_TO_NEW_PROJECT,
                DATASET_IMPORT_STATUSES.TASK_TYPE_SELECTION_TO_NEW_PROJECT,
                DATASET_IMPORT_STATUSES.READY,
            ]) &&
            !isEmpty(uploadId) &&
            !isEmpty(projectName) &&
            !isEmpty(taskType) &&
            !isEmpty(datasetImportItem?.labels) &&
            (datasetImportItem?.taskType?.includes('classification') ? datasetImportItem?.labels.length >= 2 : true)
        );
    };

    const prepareDataset = (file: File): string => {
        const { name: fileName, type: fileType, size: fileSize, lastModified: fileLastModified } = file;
        const id = `${idMatchingFormat(fileName)}-${fileType}-${fileSize}-${fileLastModified}`;

        const datasetImportInitialState = getDatasetImportInitialState({
            id,
            name: fileName,
            size: getFileSize(file.size),
        });

        putLsDatasetImport(datasetImportInitialState);
        const onThrottleProgress = throttleProgress(() => getLsDatasetImport(id));

        const upload = uploadFile({
            file,
            endpoint: router.DATASET.IMPORT_TUS(workspaceIdentifier),
            onError: onErrorMessage((message: string): void => {
                patchLsDatasetImport({ id, progress: 0, status: DATASET_IMPORT_STATUSES.IMPORTING_ERROR });
                addNotification({ message, type: NOTIFICATION_TYPE.ERROR });
            }),
            onProgress: onThrottleProgress((datasetImportItem, bytesSent, bytesTotal): void => {
                const uploadId = getUploadId(upload.url);
                const { startFromBytes, startAt } = datasetImportItem;

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

    const prepareDatasetAction = (id: string, uploadId: string | null): void => {
        if (!uploadId) {
            patchLsDatasetImport({
                id,
                progress: 0,
                status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR,
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

        prepareDatasetForNewProject.mutate(
            { ...workspaceIdentifier, uploadId, setAbortController },
            {
                onSuccess: ({ warnings, supportedProjectTypes }) => {
                    patchLsDatasetImport(
                        formatDatasetPrepareImportResponse({
                            id,
                            uploadId,
                            warnings,
                            supportedProjectTypes,
                        })
                    );
                },
                onError: (error) => {
                    patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.PREPARING_ERROR });
                    addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
                },
            }
        );
    };

    const prepareDatasetActionJob = (id: string, uploadId: string | null): void => {
        if (!uploadId) {
            patchLsDatasetImport({
                id,
                progress: 0,
                status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR,
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

        prepareDatasetJob.mutate(
            { ...workspaceIdentifier, uploadId, setAbortController },
            {
                onSuccess: ({ jobId }) => {
                    patchLsDatasetImport({ id, preparingJobId: jobId });
                },
                onError: (error) => {
                    patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.PREPARING_ERROR });
                    addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
                },
            }
        );
    };

    const importDataset = (id: string): void => {
        const { uploadId, labels, labelColorMap, projectName, taskType } = getLsDatasetImport(
            id
        ) as DatasetImportToNewProjectItem;

        if (!uploadId) {
            patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR });
            addNotification({ message: `Upload ${uploadId} not found`, type: NOTIFICATION_TYPE.ERROR });

            return;
        }

        if (taskType === null) {
            return;
        }

        patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT });

        const labelsWithColors = labels.map((label: DatasetImportLabel) => {
            return { ...label, color: labelColorMap[label.name] ?? getRandomDistinctColor() };
        });

        importDatasetToNewProject.mutate(
            {
                organizationId,
                workspaceId,
                projectData: { uploadId, projectName: projectName.trim(), taskType, labels: labelsWithColors },
                setAbortController,
                anomalyRevamp: FEATURE_FLAG_ANOMALY_REDUCTION,
            },
            {
                onSuccess: async () => {
                    await deleteDatasetAfterImporting(id);
                },
                onError: (error: AxiosError) => {
                    patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR });
                    addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
                },
            }
        );
    };

    const importDatasetJob = (id: string): void => {
        const { uploadId, labels, labelColorMap, projectName, taskType } = getLsDatasetImport(
            id
        ) as DatasetImportToNewProjectItem;

        if (!uploadId) {
            patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR });
            addNotification({ message: `Upload ${uploadId} not found`, type: NOTIFICATION_TYPE.ERROR });

            return;
        }

        if (taskType === null) {
            return;
        }

        patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT });

        const labelsWithColors = labels.map((label: DatasetImportLabel) => {
            return { ...label, color: labelColorMap[label.name] ?? getRandomDistinctColor() };
        });

        importDatasetToNewProjectJob.mutate(
            {
                organizationId,
                workspaceId,
                projectData: { uploadId, projectName: projectName.trim(), taskType, labels: labelsWithColors },
                setAbortController,
                anomalyRevamp: FEATURE_FLAG_ANOMALY_REDUCTION,
            },
            {
                onSuccess: ({ jobId }) => patchLsDatasetImport({ id, importingJobId: jobId }),
                onError: (error: AxiosError) => {
                    patchLsDatasetImport({ id, status: DATASET_IMPORT_STATUSES.IMPORTING_TO_NEW_PROJECT_ERROR });
                    addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
                },
            }
        );
    };

    const abortDatasetImportAction = runWhenTruthy((uploadId: string) => {
        abortControllers.get(uploadId)?.abort();
        abortControllers.delete(uploadId) && setAbortControllers(new Map(abortControllers));
    });

    return (
        <DatasetImportToNewProjectContext.Provider
            value={{
                isReady,
                isDeleting: deleteImportProjectFromDataset.isPending,
                setActiveDatasetImportId,

                activeDatasetImport,

                patchActiveDatasetImport,
                deleteTemporallyDatasetImport,

                prepareDataset,
                prepareDatasetAction,
                prepareDatasetActionJob,

                importDataset,
                importDatasetJob,

                abortDatasetImportAction,

                datasetImports: lsDatasetImports ?? [],

                patchDatasetImport: patchLsDatasetImport,
                deleteDatasetImport: deleteLsDatasetImport,
            }}
        >
            {children}
        </DatasetImportToNewProjectContext.Provider>
    );
};

export const useDatasetImportToNewProject = (): DatasetImportContextProps => {
    const context = useContext(DatasetImportToNewProjectContext);

    if (context === undefined) {
        throw new MissingProviderError('useDatasetImportToNewProject', 'DatasetImportToNewProjectProvider');
    }

    return context;
};
