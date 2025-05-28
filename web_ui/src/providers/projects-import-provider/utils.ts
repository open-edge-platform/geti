// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceIdentifier } from '@geti/core/src/workspaces/services/workspaces.interface';

import { LOCAL_STORAGE_KEYS } from '../../shared/local-storage-keys';
import { getParsedLocalStorage, isNonEmptyString, setParsedLocalStorage } from '../../shared/utils';
import {
    ProjectImportBase,
    ProjectImportingStatus,
    ProjectImportItem,
    ProjectImportItems,
    ProjectImportStatusValues,
} from './project-import.interface';

export const getProjectImportItemsKey = ({ organizationId, workspaceId }: WorkspaceIdentifier) => {
    return `${LOCAL_STORAGE_KEYS.IMPORTING_PROJECT}-${organizationId}-${workspaceId}`;
};

export const getProjectImportItems = (workspaceIdentifier: WorkspaceIdentifier) => {
    const importProjectItemsInWorkspaceContext = getParsedLocalStorage<ProjectImportItems>(
        getProjectImportItemsKey(workspaceIdentifier)
    );

    if (importProjectItemsInWorkspaceContext === null) {
        return getParsedLocalStorage<ProjectImportItems>(LOCAL_STORAGE_KEYS.IMPORTING_PROJECT);
    }

    return importProjectItemsInWorkspaceContext;
};

export const setProjectImportItems = (workspaceIdentifier: WorkspaceIdentifier, importItems: ProjectImportItems) => {
    setParsedLocalStorage(getProjectImportItemsKey(workspaceIdentifier), importItems);
};

export const getProjectImportItem = (
    workspaceIdentifier: WorkspaceIdentifier,
    fileId: string
): ProjectImportItem | null => {
    const importItemsLS = getProjectImportItems(workspaceIdentifier);

    return !importItemsLS ? null : (importItemsLS[fileId] ?? null);
};

export const isProjectImportingStatus = (
    item: ProjectImportItem
): item is ProjectImportingStatus & ProjectImportBase => {
    return [ProjectImportStatusValues.IMPORTING, ProjectImportStatusValues.IMPORTING_INTERRUPTED].includes(item.status);
};

export const getProjectStatusBaseData = ({
    fileId,
    fileSize,
    fileName,
    options,
}: ProjectImportItem): ProjectImportBase => ({
    fileId,
    fileSize,
    fileName,
    options,
});

export const getImportProjectId = (uploadItemUrl: string | null): string => {
    return isNonEmptyString(uploadItemUrl) ? uploadItemUrl.split('resumable/')[1] : '';
};
