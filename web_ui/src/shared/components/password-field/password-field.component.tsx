// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
