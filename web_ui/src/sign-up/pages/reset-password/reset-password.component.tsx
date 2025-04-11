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

import { FormEvent, useState } from 'react';

import { Form, Heading, Text } from '@adobe/react-spectrum';
import { ValidationError } from 'yup';

import { useResetPassword } from '../../../core/users/hook/use-users.hook';
import { isYupValidationError } from '../../../pages/user-management/profile-page/utils';
import { PasswordState } from '../../../pages/user-management/users/add-member-popup/add-member-popup.interface';
import {
    defaultPasswordState,
    handlePassword,
    validatePasswordsSchema,
} from '../../../pages/user-management/users/add-member-popup/utils';
import { Button } from '../../../shared/components/button/button.component';
import { InvalidTokenAlert } from '../../../shared/components/invalid-token-alert/invalid-token-alert.component';
import { PasswordField } from '../../../shared/components/password-field/password-field.component';
import { CONFIRM_PASSWORD_ERROR_MESSAGE, encodeToBase64 } from '../../../shared/utils';
import { useEmailToken } from '../../hooks/use-email-token/use-email-token.hook';
import { BackgroundLayout } from '../../shared/background-layout/background-layout.component';
import { PrivacyTermsOfUseFooter } from '../../shared/privacy-terms-of-use-footer/privacy-terms-of-use-footer.component';
import { handleErrorMessageState } from '../registration/utils';

import sharedClasses from '../../../shared/shared.module.scss';
import classes from './reset-password.module.scss';

export const ResetPassword = (): JSX.Element => {
    const emailToken = useEmailToken();
    const [password, setPassword] = useState<PasswordState>(defaultPasswordState);
    const [confirmPassword, setConfirmPassword] = useState<PasswordState>(defaultPasswordState);

    const resetPassword = useResetPassword();

    const emailTokenIsInvalid = emailToken.token === null;

    const isBtnDisabled =
        !confirmPassword.value || !password.value || !!confirmPassword.error || !!password.error || emailTokenIsInvalid;

    const handleResetPassword = (event: FormEvent): void => {
        event.preventDefault();

        if (emailTokenIsInvalid) {
            return;
        }

        try {
            validatePasswordsSchema.validateSync(
                { password: password.value, confirmPassword: confirmPassword.value },
                { abortEarly: false }
            );

            resetPassword.mutate({ token: emailToken.token, new_password: encodeToBase64(password.value) });
        } catch (error: unknown) {
            if (isYupValidationError(error)) {
                error.inner.forEach(({ path, message }: ValidationError) => {
                    if (path === 'password') {
                        setPassword(handleErrorMessageState(message));
                    } else if (path === 'confirmPassword') {
                        setConfirmPassword(handleErrorMessageState(CONFIRM_PASSWORD_ERROR_MESSAGE));
                    }
                });
            }
        }
    };

    return (
        <BackgroundLayout className={resetPassword.isPending ? sharedClasses.contentDisabled : ''}>
            <Heading
                level={1}
                margin={0}
                marginBottom={'size-100'}
                UNSAFE_className={classes.title}
                id={'reset-password-id'}
            >
                Create new password
            </Heading>
            {emailToken.token !== null ? (
                <Text data-testid={'for-email-id'} UNSAFE_className={classes.createPasswordEmail}>
                    for <b>{emailToken.email}</b>
                </Text>
            ) : null}
            <Form marginY={'size-400'} onSubmit={handleResetPassword}>
                <PasswordField
                    label={'New password'}
                    value={password.value}
                    error={password.error}
                    onChange={handlePassword(setPassword)}
                    autoComplete='off'
                    isNewPassword
                    isDisabled={emailTokenIsInvalid}
                />
                <PasswordField
                    label={'Confirm new password'}
                    value={confirmPassword.value}
                    error={confirmPassword.error}
                    onChange={handlePassword(setConfirmPassword)}
                    autoComplete='off'
                    isDisabled={emailTokenIsInvalid}
                />

                <InvalidTokenAlert
                    isVisible={emailTokenIsInvalid}
                    message={emailToken.token === null ? emailToken.error : ''}
                    styles={{ marginBottom: 'size-100' }}
                />
                <Button
                    type={'submit'}
                    isPending={resetPassword.isPending}
                    isDisabled={isBtnDisabled}
                    UNSAFE_className={classes.submitBtn}
                    alignSelf={'end'}
                    width={'auto'}
                >
                    Submit new password
                </Button>
            </Form>
            <PrivacyTermsOfUseFooter />
        </BackgroundLayout>
    );
};
