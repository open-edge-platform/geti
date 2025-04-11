// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import isEmpty from 'lodash/isEmpty';

import { getVideoDimensionErrors, isVideoFile, loadVideoFromFile, VALIDATION_RULES } from '../../shared/media-utils';
import { getFileSize } from '../../shared/utils';

export const VALIDATION_MESSAGES = {
    IMAGE: {
        MAX_SIZE: `Image size should be less than or equal ${getFileSize(VALIDATION_RULES.INDEXED_DB.MAX_SIZE, {
            base: 2,
        })}`,
    },

    VIDEO: {
        MAX_SIZE: `Video size should be less than or equal ${getFileSize(VALIDATION_RULES.INDEXED_DB.MAX_SIZE, {
            base: 2,
        })}`,
    },
};

export const validateMediaSize = (file: File): { message: string; error: boolean } => {
    const message = isVideoFile(file) ? VALIDATION_MESSAGES.VIDEO.MAX_SIZE : VALIDATION_MESSAGES.IMAGE.MAX_SIZE;

    return file.size <= VALIDATION_RULES.INDEXED_DB.MAX_SIZE ? { message, error: false } : { message, error: true };
};

// TODO: For now ignore this method as it's not being used
export const validateVideoDimensions = (validFileCallback: (videoFile: File) => void) => async (videoFile: File) => {
    const videoElement = await loadVideoFromFile(videoFile);

    videoElement.onloadedmetadata = () => {
        const errors = getVideoDimensionErrors(videoElement);

        if (isEmpty(errors)) {
            validFileCallback(videoFile);
        } else {
            // trigger notification
        }
    };
};
