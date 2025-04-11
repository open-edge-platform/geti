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

import { Dispatch, SetStateAction } from 'react';

import * as yup from 'yup';

import {
    CONFIRM_PASSWORD_ERROR_MESSAGE,
    MAX_NUMBER_OF_PASSWORD_CHARACTERS,
    PASSWORD_DOES_NOT_MEET_LENGTH_RULE,
    passwordValidationRules,
} from '../../../../shared/utils';
import { PasswordState } from './add-member-popup.interface';

export const defaultPasswordState: PasswordState = {
    value: '',
    error: '',
};

export const validatePasswordsSchema = yup.object({
    password: passwordValidationRules('Password is required'),
    confirmPassword: yup.string().oneOf([yup.ref('password')], CONFIRM_PASSWORD_ERROR_MESSAGE),
});

export const handlePassword =
    (setState: Dispatch<SetStateAction<PasswordState>>) =>
    (value: string): void => {
        if (value.length > MAX_NUMBER_OF_PASSWORD_CHARACTERS) {
            setState((prevState) => ({ ...prevState, error: PASSWORD_DOES_NOT_MEET_LENGTH_RULE }));
        } else {
            setState(() => ({ error: '', value }));
        }
    };
