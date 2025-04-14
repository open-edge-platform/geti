// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
