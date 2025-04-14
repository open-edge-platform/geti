// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Label } from '../../core/labels/label.interface';
import { DatasetIdentifier } from '../../core/projects/dataset.interface';

interface ListItem {
    readonly uploadId: string;
    readonly datasetIdentifier: DatasetIdentifier;
    readonly file: File | undefined;
    readonly meta?: MEDIA_CONTENT_BUCKET;
    readonly fileSize: number;
    readonly fileName: string;
    readonly fileType: string;
}

export enum ValidationFailStatus {
    UNSUPPORTED_TYPE = -1,
    INVALID_DIMENSIONS = -2,
    INVALID_DURATION = -3,
    INVALID_MEDIA = -4,
    MISSING_TYPE = -5,
}

export interface ValidationFailReason {
    readonly file: File;
    readonly status: ValidationFailStatus;
    readonly errors: string[];
}

interface UploadInfoDTO {
    filename: string;
    label_ids: string[];
}

// When we finish uploading a media item we remove the file to reduce memory consumption
export type SuccessListItem = Omit<ListItem, 'file'>;

export interface QueuedListItem extends ListItem {
    readonly file: File;
    uploadInfo?: UploadInfoDTO;
}

export interface ErrorListItem extends ListItem, Pick<QueuedListItem, 'uploadInfo'> {
    readonly errors: string[];
    readonly status: number;
    readonly statusText: string | null;
}

export interface ProgressListItem extends ListItem {
    progress: number;
}

export interface UploadMedia {
    readonly datasetIdentifier: DatasetIdentifier;
    readonly files: File[];
    readonly meta?: MEDIA_CONTENT_BUCKET;
    labelIds?: string[];
    label?: Label;
}

export interface UploadStatusProgress {
    isUploading: boolean;
}

export enum MEDIA_CONTENT_BUCKET {
    NORMAL = 'Normal',
    ANOMALOUS = 'Anomalous',
    GENERIC = 'Generic',
}

export type UploadProgress = {
    [P in MEDIA_CONTENT_BUCKET]?: UploadStatusProgress;
};

export enum MediaUploadItemState {
    QUEUED = 'queued',
    PROGRESS = 'progress',
    SUCCESS = 'success',
    ERROR = 'error',
}

export type MediaUploadItem =
    | ({ type: MediaUploadItemState.ERROR } & ErrorListItem)
    | ({ type: MediaUploadItemState.SUCCESS } & SuccessListItem)
    | ({ type: MediaUploadItemState.PROGRESS } & ProgressListItem)
    | ({ type: MediaUploadItemState.QUEUED } & QueuedListItem);

export interface MediaUploadPerDataset {
    list: MediaUploadItem[];

    /* List of items (from the current dataset) that couldnt be processed */
    errorList: ErrorListItem[];

    /* List of items (from the current dataset) that were processed */
    successList: SuccessListItem[];

    /* List of items currently waiting to be processed */
    waitingQueue: QueuedListItem[];

    /* List of items currently being processed */
    processingQueue: ProgressListItem[];

    progressMap: Record<string, ProgressListItem>;
    uploadProgress: UploadProgress;

    timeUploadStarted: number | null;

    insufficientStorage: boolean;

    /* If there is any item currently still being processed */
    isUploadInProgress: boolean;

    /* Toggle for the upload status UI */
    isUploadStatusBarVisible: boolean;
}

export type MediaUploadState = Record<string /* dataset id */, MediaUploadPerDataset>;

interface MediaUploadReducerStatePerDataset {
    list: MediaUploadItem[];

    timeUploadStarted: number | null;

    insufficientStorage: boolean;
}

export type MediaUploadReducerState = Record<string /* dataset id */, MediaUploadReducerStatePerDataset>;

export interface MediaUploadProviderProps {
    children: ReactNode;
}
