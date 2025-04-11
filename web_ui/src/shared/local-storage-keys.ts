// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { WorkspaceIdentifier } from '../core/workspaces/services/workspaces.interface';

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
