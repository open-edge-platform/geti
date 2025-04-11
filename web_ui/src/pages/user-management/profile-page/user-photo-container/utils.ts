// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import {
    ImageValidationMessages,
    ImageValidationRules,
} from '../../../../providers/media-upload-provider/media-upload.validator';
import { VALIDATION_RULES } from '../../../../shared/media-utils';
import { getFileSize } from '../../../../shared/utils';

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
