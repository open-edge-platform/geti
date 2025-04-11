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
