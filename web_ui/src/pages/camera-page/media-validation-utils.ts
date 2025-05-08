// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEmpty } from 'lodash-es';

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
