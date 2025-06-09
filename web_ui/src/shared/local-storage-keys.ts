// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceIdentifier } from '@geti/core/src/workspaces/services/workspaces.interface';

export enum LOCAL_STORAGE_KEYS {
    ALL = 'all',
    PINNED_LABELS = 'pinnedLabels',
    INTENDED_PATH_BEFORE_AUTHENTICATION = 'intended-path-before-authentication',
    EXPORTING_DATASETS = 'exportingDatasets',
    EXPORTING_PROJECT = 'exportingProject',
    IMPORTING_PROJECT = 'importingProject',
    IS_ANNOTATOR_SETTINGS_UPDATED = 'is-annotator-settings-updated',
    IMPORT_DATASET_TO_NEW_PROJECT = 'importDatasetToNewProject',
    IMPORT_DATASET_TO_EXISTING_PROJECT = 'importDatasetToExistingProject',
    COPY_ANNOTATION = 'copy-annotation',
    LAST_LOGIN_INFO = 'lastLoginInfo',
    MEDIA_VIEW_MODE = 'media-view-mode',
    LAST_SELECTED_ORGANIZATION_ID = 'last-selected-organization-id',
}

export const getPanelSettingsKey = (projectId: string) => {
    return `${LOCAL_STORAGE_KEYS.IS_ANNOTATOR_SETTINGS_UPDATED}-${projectId}`;
};

export const getImportDatasetToNewProjectKey = ({ workspaceId, organizationId }: WorkspaceIdentifier) => {
    return `${LOCAL_STORAGE_KEYS.IMPORT_DATASET_TO_NEW_PROJECT}-${organizationId}-${workspaceId}`;
};
