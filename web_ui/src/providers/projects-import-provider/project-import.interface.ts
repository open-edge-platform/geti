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

import { ImportOptions } from '../../core/projects/services/project-service.interface';

export interface ProjectsImportContextProps {
    importItems: ProjectImportItems;
    importProject: (file: File, options: ImportOptions) => void;
    cancelImportProject: (fileId: string) => Promise<void>;
    removeImportProjectItemFromLS: (fileId: string) => void;
    patchImportProjectItem: (fileId: string, importItem: ProjectImportItem<null>) => void;
}

export enum ProjectImportStatusValues {
    IMPORTING = 'IMPORTING', // SENDING FILE TO THE SERVER
    IMPORTING_INTERRUPTED = 'IMPORTING_INTERRUPTED', // SENDING FILE INTERRUPTED
    CREATING = 'CREATING', // SERVER IS CREATING A PROJECT
    CREATED = 'CREATED', // SERVER CREATED A PROJECT
    ERROR = 'ERROR', // ERROR, E.G. PROJECT ALREADY EXISTS, ERROR WHILE SENDING FILE TO THE SERVER
}

export interface ProjectImportBase {
    fileId: string;
    fileName: string;
    fileSize: number;
    options: ImportOptions;
}

export interface ProjectImportingStatus {
    status: ProjectImportStatusValues.IMPORTING;
    progress: number;
    timeRemaining: string | null;
    bytesRemaining: string | null;
    startImportTime: number;
    bytesUploaded: number;
}

interface ProjectImportInterruptedStatus {
    status: ProjectImportStatusValues.IMPORTING_INTERRUPTED;
}

export interface ProjectCreatingStatus {
    status: ProjectImportStatusValues.CREATING;
    importProjectId: string;
}

interface ProjectCreatedStatus {
    status: ProjectImportStatusValues.CREATED;
}

interface ProjectCreatingError {
    status: ProjectImportStatusValues.ERROR;
}

type ProjectItemStatus =
    | ProjectImportingStatus
    | ProjectImportInterruptedStatus
    | ProjectCreatingStatus
    | ProjectCreatedStatus
    | ProjectCreatingError;

export type ProjectImportItem<T extends ProjectImportBase | null = ProjectImportBase> = T extends ProjectImportBase
    ? ProjectItemStatus & ProjectImportBase
    : ProjectItemStatus;

export type ProjectImportItems = Record<string /* file id */, ProjectImportItem>;
