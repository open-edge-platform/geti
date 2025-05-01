// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction } from 'react';

import {
    CONFIRM_PASSWORD_ERROR_MESSAGE,
    MAX_NUMBER_OF_PASSWORD_CHARACTERS,
    PASSWORD_DOES_NOT_MEET_LENGTH_RULE,
    passwordValidationRules,
} from '@shared/utils';
import * as yup from 'yup';

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
