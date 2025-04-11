// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import * as yup from 'yup';

import { CONFIRM_PASSWORD_ERROR_MESSAGE, passwordValidationRules } from '../../../../shared/utils';
import { PasswordState } from '../../users/add-member-popup/add-member-popup.interface';

export const passwordSchema = yup.object({
    oldPassword: yup.string().required('Old password is required'),
    newPassword: passwordValidationRules('New password is required'),
    confirmPassword: yup.string().oneOf([yup.ref('newPassword')], CONFIRM_PASSWORD_ERROR_MESSAGE),
});

export const defaultPassword: PasswordState = {
    value: '',
    error: '',
};

export enum ErrorUserManagementMessages {
    WRONG_OLD_PASSWORD = "That's an incorrect password. Try again.",
    SAME_NEW_PASSWORD = 'Password should be different from your old password.',
}
