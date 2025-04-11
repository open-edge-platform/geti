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

import { useState } from 'react';

import { Flex, TextField } from '@adobe/react-spectrum';
import { View } from '@react-spectrum/view';
import { SpectrumTextFieldProps } from '@react-types/textfield';

import { Alert, Invisible, Visible } from '../../../assets/icons';
import { idMatchingFormat } from '../../../test-utils/id-utils';
import { NEW_PASSWORD_ERROR_MESSAGE } from '../../utils';
import { ActionButton } from '../button/button.component';

import textFieldClasses from '../../../pages/user-management/profile-page/profile-page.module.scss';
import classes from './password-field.module.scss';

interface PasswordFieldProps extends SpectrumTextFieldProps {
    isNewPassword?: boolean;
    error: string;
}

export const PasswordField = (props: PasswordFieldProps): JSX.Element => {
    const { isNewPassword, error, label } = props;
    const [showPassword, setShowPassword] = useState<boolean>(false);

    const togglePassword = (): void => {
        setShowPassword((prev: boolean) => !prev);
    };

    const errorId = label ? `${idMatchingFormat(label as string)}-error-msg` : 'password-error-msg';

    return (
        <View UNSAFE_className={classes.passwordFieldBox} marginBottom={'size-200'} position='relative'>
            <View position={'relative'}>
                <TextField
                    type={showPassword ? 'text' : 'password'}
                    width='100%'
                    UNSAFE_className={[
                        textFieldClasses.textField,
                        classes.passwordField,
                        error ? classes.passwordFieldError : '',
                    ].join(' ')}
                    {...props}
                />
                <Flex
                    alignItems='center'
                    marginTop='size-225'
                    UNSAFE_className={classes.textInputIcons}
                    marginEnd={!!error ? 'size-100' : 0}
                >
                    <ActionButton UNSAFE_className={classes.iconButton} onPress={togglePassword}>
                        {showPassword ? <Visible className={classes.icon} /> : <Invisible className={classes.icon} />}
                    </ActionButton>
                    {error ? <Alert className={classes.alertIcon} /> : <></>}
                </Flex>
            </View>
            {error ? (
                <span className={[classes.tip, classes.errorMsg].join(' ')} data-testid={errorId} id={errorId}>
                    {error}
                </span>
            ) : (
                isNewPassword && (
                    <span
                        className={[classes.tip, classes.newPassword].join(' ')}
                        data-testid='new-password-rule-msg'
                        id='new-password-rule-msg'
                    >
                        {NEW_PASSWORD_ERROR_MESSAGE}
                    </span>
                )
            )}
        </View>
    );
};
