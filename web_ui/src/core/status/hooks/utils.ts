// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getFileSize } from '../../../shared/utils';

export const LOW_FREE_DISK_SPACE_IN_BYTES = 2e10;
export const TOO_LOW_FREE_DISK_SPACE_IN_BYTES = 1.5e10;

export const isBelowTooLowFreeDiskSpace = (freeSpace: number | undefined) =>
    freeSpace !== undefined && freeSpace <= TOO_LOW_FREE_DISK_SPACE_IN_BYTES;

export const isBelowLowFreeDiskSpace = (freeSpace: number) => freeSpace <= LOW_FREE_DISK_SPACE_IN_BYTES;

export const LOW_FREE_DISK_SPACE_MESSAGE =
    `Your storage is running low: less than ${getFileSize(LOW_FREE_DISK_SPACE_IN_BYTES)} available. Below ` +
    `${getFileSize(TOO_LOW_FREE_DISK_SPACE_IN_BYTES)} many operations such as upload, annotate, ` +
    'or training, are disabled. Please remove unnecessary objects (e.g. projects, datasets) to reclaim space.';

export const TOO_LOW_FREE_DISK_SPACE_MESSAGE =
    `Your storage is too low: less than ${getFileSize(TOO_LOW_FREE_DISK_SPACE_IN_BYTES)} available. ` +
    'Please remove unnecessary objects (e.g. projects, datasets) ' +
    "otherwise you won't be able to upload, annotate or train models.";
