// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, useState } from 'react';

import { Flex, TextField, View } from '@adobe/react-spectrum';

import { Alert, Invisible, Visible } from '../../icons';
import { ActionButton } from '../button/button.component';

import classes from './password-field.module.scss';

const NEW_PASSWORD_ERROR_MESSAGE =
    'Password must consist of 8 - 200 characters, at least one capital letter, lower letter, digit or symbol.';

type TextFieldProps = ComponentProps<typeof TextField>;

interface PasswordFieldProps extends Omit<TextFieldProps, 'label'> {
    isNewPassword?: boolean;
    error: string;
    label?: string;
}

export const PasswordField = (props: PasswordFieldProps): JSX.Element => {
    const { isNewPassword, error, label } = props;
    const [showPassword, setShowPassword] = useState<boolean>(false);

    const togglePassword = (): void => {
        setShowPassword((prev: boolean) => !prev);
    };

    const errorId = label ? `${label.split(' ').join('-').toLocaleLowerCase()}-error-msg` : 'password-error-msg';

    return (
        <View UNSAFE_className={classes.passwordFieldBox} marginBottom={'size-200'} position='relative'>
            <View position={'relative'}>
                <TextField
                    label={label}
                    type={showPassword ? 'text' : 'password'}
                    width='100%'
                    UNSAFE_className={[
                        classes.textField,
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
                <span className={[classes.tip, classes.errorMsg].join(' ')} data-testid={errorId}>
                    {error}
                </span>
            ) : (
                isNewPassword && (
                    <span className={[classes.tip, classes.newPassword].join(' ')} data-testid='new-password-rule-msg'>
                        {NEW_PASSWORD_ERROR_MESSAGE}
                    </span>
                )
            )}
        </View>
    );
};
