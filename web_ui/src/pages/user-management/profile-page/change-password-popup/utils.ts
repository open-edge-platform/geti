// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
