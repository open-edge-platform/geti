// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useCallback, useContext, useEffect, useRef, useState } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { isEmpty, isEqual } from 'lodash-es';
import { DetailedError, Upload } from 'tus-js-client';

import { useImportProject } from '../../core/projects/hooks/use-import-project.hook';
import { ImportOptions } from '../../core/projects/services/project-service.interface';
import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../notification/notification.component';
import { MissingProviderError } from '../../shared/missing-provider-error';
import { idMatchingFormat } from '../../test-utils/id-utils';
import { getBytesRemaining, getTimeRemaining } from '../dataset-import-to-new-project-provider/utils';
import { useTusUpload } from '../tus-upload-provider/tus-upload-provider.component';
import { getTUSErrorMessage } from '../tus-upload-provider/util';
import { useWorkspaceIdentifier } from '../workspaces-provider/use-workspace-identifier.hook';
import {
    ProjectImportItem,
    ProjectImportItems,
    ProjectImportStatusValues,
    ProjectsImportContextProps,
} from './project-import.interface';
import {
    getImportProjectId,
    getProjectImportItem,
    getProjectImportItems,
    getProjectStatusBaseData,
    isProjectImportingStatus,
    setProjectImportItems,
} from './utils';

const ProjectsImportContext = createContext<ProjectsImportContextProps | undefined>(undefined);

interface ProjectsImportProviderProps {
    children: ReactNode;
}

export const ProjectsImportProvider = ({ children }: ProjectsImportProviderProps): JSX.Element => {
    const { useImportProjectMutation } = useImportProject();
    const importProjectMutation = useImportProjectMutation();

    const workspaceIdentifier = useWorkspaceIdentifier();

    const [importItems, setImportItems] = useState<ProjectImportItems>(
        () => getProjectImportItems(workspaceIdentifier) ?? {}
    );

    const { addNotification } = useNotification();
    const { uploadFile } = useTusUpload();
    const pendingUploads = useRef(new Map<string, Upload>());

    const putImportProjectItem = useCallback(
        (inputImportItems: ProjectImportItems): void => {
            const importItemsLS = getProjectImportItems(workspaceIdentifier);

            const newImportItems = { ...importItemsLS, ...inputImportItems };

            setProjectImportItems(workspaceIdentifier, newImportItems);
            setImportItems(newImportItems);
        },
        [workspaceIdentifier]
    );

    const patchImportProjectItem = useCallback(
        (fileId: string, importItem: ProjectImportItem<null>): void => {
            const currentProjectImportItem = getProjectImportItem(workspaceIdentifier, fileId);

            if (!currentProjectImportItem) {
                return;
            }

            const baseProjectItemData = getProjectStatusBaseData(currentProjectImportItem);

            putImportProjectItem({
                [fileId]: {
                    ...baseProjectItemData,
                    ...importItem,
                },
            });
        },
        [workspaceIdentifier, putImportProjectItem]
    );

    const onUploadProgress = useCallback(
        (fileId: string, bytesUploaded: number, bytesTotal: number) => {
            const importItem = getProjectImportItem(workspaceIdentifier, fileId);

            if (!importItem || !isProjectImportingStatus(importItem)) {
                return;
            }

            patchImportProjectItem(fileId, {
                ...importItem,
                progress: Math.floor((bytesUploaded / bytesTotal) * 100),
                timeRemaining: getTimeRemaining(importItem.startImportTime, bytesUploaded, bytesTotal - bytesUploaded),
                bytesRemaining: getBytesRemaining(bytesTotal - bytesUploaded),
                bytesUploaded,
            });
        },
        [patchImportProjectItem, workspaceIdentifier]
    );

    const onImportProjectSuccess = useCallback(
        async (fileId: string, importProjectId: string, options: ImportOptions): Promise<void> => {
            await importProjectMutation.mutateAsync(
                { identifier: { ...workspaceIdentifier, importProjectId }, options },
                {
                    onSuccess: (jobData) => {
                        patchImportProjectItem(fileId, {
                            status: ProjectImportStatusValues.CREATING,
                            importProjectId: jobData.importProjectId,
                        });
                    },
                }
            );

            return;
        },
        [importProjectMutation, patchImportProjectItem, workspaceIdentifier]
    );

    const { router } = useApplicationServices();
    const importProject = useCallback(
        (file: File, options: ImportOptions): void => {
            const { name, type, lastModified, size } = file;
            const fileId = idMatchingFormat(`${name}-${type}-${size}-${lastModified}`);

            const upload = uploadFile({
                file,
                endpoint: router.PROJECT_IMPORT.IMPORT_TUS(workspaceIdentifier),
                onProgress: (bytesUploaded, bytesTotal): void => {
                    onUploadProgress(fileId, bytesUploaded, bytesTotal);
                },
                onSuccess: async (): Promise<void> => {
                    const importProjectId = getImportProjectId(upload.url);

                    await onImportProjectSuccess(fileId, importProjectId, options);
                },
                onError: (error: Error | DetailedError): void => {
                    const message = getTUSErrorMessage(error);

                    patchImportProjectItem(fileId, { status: ProjectImportStatusValues.ERROR });
                    addNotification({ message, type: NOTIFICATION_TYPE.ERROR });
                },
            });

            const importItem: ProjectImportItems = {
                [fileId]: {
                    fileId,
                    fileName: name,
                    fileSize: size,
                    status: ProjectImportStatusValues.IMPORTING,
                    progress: 0,
                    bytesUploaded: 0,
                    bytesRemaining: null,
                    timeRemaining: null,
                    startImportTime: Date.now(),
                    options,
                },
            };

            putImportProjectItem(importItem);

            pendingUploads.current.set(fileId, upload);
        },

        // eslint-disable-next-line react-hooks/exhaustive-deps
        [workspaceIdentifier, patchImportProjectItem, onImportProjectSuccess, onUploadProgress]
    );

    const cancelImportProject = async (fileId: string): Promise<void> => {
        const importItemToCancel = getProjectImportItem(workspaceIdentifier, fileId);

        if (!importItemToCancel) {
            return;
        }

        pendingUploads.current.get(fileId)?.abort();
        pendingUploads.current.delete(fileId);

        removeImportProjectItemFromLS(fileId);
    };

    const removeImportProjectItemFromLS = useCallback(
        (fileId: string): void => {
            const newImportItems = getProjectImportItems(workspaceIdentifier) ?? {};

            if (!newImportItems[fileId]) {
                return;
            }

            delete newImportItems[fileId];

            setProjectImportItems(workspaceIdentifier, newImportItems);
            setImportItems(newImportItems);
        },
        [workspaceIdentifier]
    );

    useEffect(() => {
        const importItemsLS = getProjectImportItems(workspaceIdentifier) ?? {};

        if (isEmpty(importItemsLS)) {
            return;
        }

        const newImportItems: ProjectImportItems = Object.entries(importItemsLS).reduce<ProjectImportItems>(
            (prev, [fileId, item]) => {
                if (item.status === ProjectImportStatusValues.IMPORTING) {
                    prev[fileId] = { ...item, status: ProjectImportStatusValues.IMPORTING_INTERRUPTED };

                    return prev;
                }

                prev[fileId] = item;

                return prev;
            },
            {}
        );

        setImportItems(newImportItems);

        if (!isEqual(importItemsLS, newImportItems)) {
            setProjectImportItems(workspaceIdentifier, newImportItems);
        }
    }, [workspaceIdentifier]);

    useEffect(() => {
        if (isEmpty(importItems)) {
            return;
        }

        Object.values(importItems).forEach(({ status, fileId }) => {
            // we can either set "CREATED" status and remove project item from local storage here
            // or remove status "CREATED" and then remove from local storage in onDone callback
            // I feel that doing it reactively to status is better
            if ([ProjectImportStatusValues.CREATED, ProjectImportStatusValues.ERROR].includes(status)) {
                removeImportProjectItemFromLS(fileId);
                return;
            }
        });
    }, [importItems, onImportProjectSuccess, removeImportProjectItemFromLS]);

    const value: ProjectsImportContextProps = {
        importProject,
        importItems,
        cancelImportProject,
        patchImportProjectItem,
        removeImportProjectItemFromLS,
    };

    return <ProjectsImportContext.Provider value={value}>{children}</ProjectsImportContext.Provider>;
};

export const useProjectsImportProvider = (): ProjectsImportContextProps => {
    const context = useContext(ProjectsImportContext);

    if (context === undefined) {
        throw new MissingProviderError('useProjectsImportProvider', 'ProjectsImportProvider');
    }

    return context;
};
