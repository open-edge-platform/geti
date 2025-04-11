// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
