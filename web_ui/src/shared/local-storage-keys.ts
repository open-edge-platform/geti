// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceIdentifier } from '@geti/core/src/workspaces/services/workspaces.interface';

export enum LOCAL_STORAGE_KEYS {
    ALL = 'all',
    UPLOADS = 'uploads',
    PINNED_LABELS = 'pinnedLabels',
    UNAUTHORIZED = 'unauthorized',
    INTENDED_PATH_BEFORE_AUTHENTICATION = 'intended-path-before-authentication',
    SERVICE_UNAVAILABLE = 'service-unavailable',
    EXPORTING_DATASETS = 'exportingDatasets',
    EXPORTING_PROJECT = 'exportingProject',
    IMPORTING_PROJECT = 'importingProject',
    IS_ANNOTATOR_SETTINGS_UPDATED = 'is-annotator-settings-updated',
    IMPORT_DATASET_TO_NEW_PROJECT = 'importDatasetToNewProject',
    IMPORT_DATASET_TO_EXISTING_PROJECT = 'importDatasetToExistingProject',
    COPY_ANNOTATION = 'copy-annotation',
    PROJECT_ACCESS_DENIED = 'projectAccessDenied',
    SELECTED_ORGANIZATION = 'selectedOrganization',
    LAST_LOGIN_INFO = 'lastLoginInfo',
    MEDIA_VIEW_MODE = 'media-view-mode',
}

export const getPanelSettingsKey = (projectId: string) => {
    return `${LOCAL_STORAGE_KEYS.IS_ANNOTATOR_SETTINGS_UPDATED}-${projectId}`;
};

export const getImportDatasetToNewProjectKey = ({ workspaceId, organizationId }: WorkspaceIdentifier) => {
    return `${LOCAL_STORAGE_KEYS.IMPORT_DATASET_TO_NEW_PROJECT}-${organizationId}-${workspaceId}`;
};
