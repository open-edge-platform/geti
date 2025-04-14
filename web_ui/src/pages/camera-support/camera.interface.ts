// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export enum FacingMode {
    USER = 'user',
    ENVIRONMENT = 'environment',
    LEFT = 'left',
    RIGHT = 'right',
}

export interface Screenshot {
    id: string;
    file: File;
    dataUrl?: string | null | undefined;
    labelIds: string[];
    labelName: string | null;
    isAccepted?: boolean;
}

export enum UserCameraPermission {
    GRANTED = 'granted',
    DENIED = 'denied',
    ERRORED = 'errored',
    PENDING = 'pending',
}

// For now we only care about these two. For the complete list please check
// https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
export enum UserCameraPermissionError {
    NOT_ALLOWED = 'NotAllowedError',
    NOT_FOUND = 'NotFoundError',
}

export const GETI_CAMERA_INDEXEDDB_INSTANCE_NAME = 'geti-camera';
