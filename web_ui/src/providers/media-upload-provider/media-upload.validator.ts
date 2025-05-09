// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEmpty } from 'lodash-es';

import {
    defineMediaType,
    getFileExtensionFromName,
    isTiffFormat,
    MEDIA_FILE_TYPE,
    VALIDATION_MESSAGES,
    VALIDATION_RULES,
} from '../../shared/media-utils';
import { ValidationFailReason, ValidationFailStatus } from './media-upload.interface';

export interface ImageValidationRules {
    MIN_WIDTH: number;
    MAX_WIDTH: number;
    MIN_HEIGHT: number;
    MAX_HEIGHT: number;
    MAX_SIZE: number;
}

export type ImageValidationMessages = Record<keyof ImageValidationRules | 'NOT_VALID_IMAGE', string>;

export const mediaExtensionHandler = (extensions: string[]): string => extensions.map((ext) => `.${ext}`).join(', ');

export const validateImage = (
    file: File,
    rules: ImageValidationRules,
    errorMessages: ImageValidationMessages
): Promise<File> => {
    // TIFs aren't a guarantee on the web, so we can't expect it to be loaded and the onload event will not be triggered
    // In this case, just pass it as is to be verified by server (https://stackoverflow.com/questions/23345194)
    if (isTiffFormat(file)) return Promise.resolve(file);

    // The only validation done on the UI side without actually opening the image is the size.
    // The rest will be validated on the server side
    if (file.size > rules.MAX_SIZE) {
        return Promise.reject({
            file,
            errors: [errorMessages.MAX_SIZE],
            status: ValidationFailStatus.INVALID_DIMENSIONS,
        });
    }

    return Promise.resolve(file);
};

const validateVideo = (file: File): Promise<File> => {
    return new Promise<File>(async (resolve, reject) => {
        if (file.size > VALIDATION_RULES.MAX_SIZE) {
            reject({
                file,
                errors: [VALIDATION_MESSAGES.VIDEO.MAX_SIZE],
                status: ValidationFailStatus.INVALID_DIMENSIONS,
            });

            return;
        }

        // In case of an AVI video, duration validation will be processed on server side.
        // There is no possibility to playback HTML5 video element with AVI media file source.
        // Event listener would not work in this case.
        // https://stackoverflow.com/questions/4129674/does-html5-video-playback-support-the-avi-format
        if (
            file.type.toLocaleLowerCase().endsWith('avi') ||
            file.type.toLocaleLowerCase().endsWith('x-msvideo') ||
            getFileExtensionFromName(file) === 'avi'
        ) {
            resolve(file);

            return;
        }

        return resolve(file);
    });
};

export const validateMedia = (file: File): Promise<File> => {
    switch (defineMediaType(file)) {
        case MEDIA_FILE_TYPE.IMAGE:
            return validateImage(
                file,
                {
                    ...VALIDATION_RULES.IMAGE,
                    MIN_HEIGHT: VALIDATION_RULES.MIN_HEIGHT,
                    MIN_WIDTH: VALIDATION_RULES.MIN_WIDTH,
                    MAX_SIZE: VALIDATION_RULES.MAX_SIZE,
                },
                VALIDATION_MESSAGES.IMAGE
            );
        case MEDIA_FILE_TYPE.VIDEO:
            return validateVideo(file);
        case MEDIA_FILE_TYPE.UNKNOWN:
            return Promise.reject({
                file,
                status: ValidationFailStatus.UNSUPPORTED_TYPE,
                errors: [VALIDATION_MESSAGES.UNSUPPORTED_MEDIA_TYPE],
            });
        case undefined:
            // This means the file type is absent null/empty/undefined.
            // It happens for instance if the user is uploading/dragging a folder on firefox
            return Promise.reject({
                file,
                status: ValidationFailStatus.MISSING_TYPE,
                errors: [VALIDATION_MESSAGES.MISSING_MEDIA_TYPE],
            });
    }
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const isValidationFailReason = (error: any): error is ValidationFailReason => {
    return !isEmpty(error?.errors) && error?.status;
};
