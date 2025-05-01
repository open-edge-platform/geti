// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FormEvent, useState } from 'react';

import { Form, Heading, Text, TextField, View } from '@adobe/react-spectrum';
import { Button } from '@shared/components/button/button.component';

import { paths } from '../../../core/services/routes';
import { useForgotPassword } from '../../../core/users/hook/use-users.hook';
import { MAX_NUMBER_OF_CHARACTERS, validateEmail } from '../../../pages/user-management/users/utils';
import { BackgroundLayout } from '../../shared/background-layout/background-layout.component';

import classes from './forgot-password.module.scss';
import sharedClasses from '@shared/shared.module.scss';

export const ForgotPassword = (): JSX.Element => {
    const [email, setEmail] = useState<string>('');
    const [showForgotPasswordForm, setShowForgotPasswordForm] = useState<boolean>(true);

    const forgotPassword = useForgotPassword();
    const isValidEmail = validateEmail.isValidSync(email);
    const isBtnDisabled = !email || !isValidEmail;

    const handleForgotPassword = (event: FormEvent): void => {
        event.preventDefault();
        forgotPassword.mutate(
            { email },
            {
                onSuccess: () => {
                    setShowForgotPasswordForm(false);
                },
            }
        );
    };

    return (
        <BackgroundLayout height={'62rem'} className={forgotPassword.isPending ? sharedClasses.contentDisabled : ''}>
            <Heading
                level={1}
                margin={0}
                marginBottom={'size-500'}
                UNSAFE_className={classes.title}
                id={'forgot-password-title-id'}
            >
                Password recovery
            </Heading>
            {showForgotPasswordForm ? (
                <Form onSubmit={handleForgotPassword}>
                    <TextField
                        // eslint-disable-next-line jsx-a11y/no-autofocus
                        autoFocus
                        label={'Email address'}
                        marginBottom={'size-450'}
                        width={'100%'}
                        value={email}
                        onChange={setEmail}
                        validationState={!isValidEmail ? 'invalid' : undefined}
                        maxLength={MAX_NUMBER_OF_CHARACTERS}
                        isQuiet
                        id={'email-input-field-id'}
                    />
                    <Button
                        variant={'accent'}
                        type={'submit'}
                        UNSAFE_className={classes.submitBtn}
                        isDisabled={isBtnDisabled}
                        isPending={forgotPassword.isPending}
                        id={'reset-button-id'}
                    >
                        Reset
                    </Button>
                </Form>
            ) : (
                <Text data-testid={'recovery-msg-id'} UNSAFE_className={classes.passwordRecoveryConfirmation}>
                    A message has been sent to your email with further instructions.
                </Text>
            )}
            <View position={'absolute'} bottom={'size-400'}>
                <Text UNSAFE_className={classes.backSignIn}>
                    Back to{' '}
                    <a href={paths.root({})} className={classes.signInLink} id={'signin-button-id'}>
                        Sign in
                    </a>
                </Text>
            </View>
        </BackgroundLayout>
    );
};
