// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { VALIDATION_RULES } from '@shared/media-utils';
import { getFileSize } from '@shared/utils';

import {
    ImageValidationMessages,
    ImageValidationRules,
} from '../../../../providers/media-upload-provider/media-upload.validator';

export const USER_PHOTO_VALIDATION_RULES: ImageValidationRules = {
    MIN_WIDTH: VALIDATION_RULES.MIN_WIDTH,
    MIN_HEIGHT: VALIDATION_RULES.MIN_HEIGHT,
    MAX_WIDTH: VALIDATION_RULES.IMAGE.MAX_WIDTH,
    MAX_HEIGHT: VALIDATION_RULES.IMAGE.MAX_HEIGHT,
    MAX_SIZE: 0.5 * 1024 * 1024, // 0.5 MiB
};

export const USER_PHOTO_VALIDATION_MESSAGES: ImageValidationMessages = {
    MIN_WIDTH: `User photo width should be more than or equal ${USER_PHOTO_VALIDATION_RULES.MIN_WIDTH} pixels`,
    MIN_HEIGHT: `User photo height should be more than or equal ${USER_PHOTO_VALIDATION_RULES.MIN_HEIGHT} pixels`,
    MAX_WIDTH: `User photo width should be less than or equal ${USER_PHOTO_VALIDATION_RULES.MAX_WIDTH} pixels`,
    MAX_HEIGHT: `User photo height should be less than or equal ${USER_PHOTO_VALIDATION_RULES.MAX_HEIGHT} pixels`,
    MAX_SIZE: `User photo should be less than or equal ${getFileSize(USER_PHOTO_VALIDATION_RULES.MAX_SIZE, {
        base: 2,
    })}`,
    NOT_VALID_IMAGE: 'Not a valid user photo',
};
