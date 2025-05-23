// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FormEvent, useState } from 'react';

import {
    Button,
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Flex,
    Form,
    Heading,
    PasswordField,
    Text,
    TextField,
    View,
} from '@geti/ui';
import { ValidationError } from 'yup';

import { paths } from '@geti/core/src/services/routes';
import { useUserRegister } from '../../../core/users/hook/use-users.hook';
import { isYupValidationError } from '../../../pages/user-management/profile-page/utils';
import { PasswordState } from '../../../pages/user-management/users/add-member-popup/add-member-popup.interface';
import {
    defaultPasswordState,
    validatePasswordsSchema,
} from '../../../pages/user-management/users/add-member-popup/utils';
import { InvalidTokenAlert } from '../../../shared/components/invalid-token-alert/invalid-token-alert.component';
import { encodeToBase64, redirectTo } from '../../../shared/utils';
import { useEmailToken } from '../../hooks/use-email-token/use-email-token.hook';
import { handleErrorMessageState } from './utils';

import classes from './registration.module.scss';

export const Registration = (): JSX.Element => {
    const emailToken = useEmailToken();
    const [firstName, setFirstName] = useState<string>('');
    const [secondName, setSecondName] = useState<string>('');
    const [password, setPassword] = useState<PasswordState>(defaultPasswordState);
    const [confirmPassword, setConfirmPassword] = useState<PasswordState>(defaultPasswordState);

    const registerUser = useUserRegister();

    const emailTokenIsInvalid = emailToken.token === null;

    const isBtnDisabled: boolean =
        !firstName ||
        !secondName ||
        !password.value ||
        !!password.error ||
        !confirmPassword.value ||
        !!confirmPassword.error ||
        registerUser.isPending ||
        emailTokenIsInvalid;

    const handlePassword = (value: string): void => {
        setPassword(() => ({
            error: '',
            value,
        }));
    };

    const handleConfirmPassword = (value: string): void => {
        setConfirmPassword(() => ({
            error: '',
            value,
        }));
    };

    const handleSubmit = (e: FormEvent): void => {
        e.preventDefault();

        if (emailTokenIsInvalid) {
            return;
        }

        try {
            validatePasswordsSchema.validateSync(
                {
                    password: password.value,
                    confirmPassword: confirmPassword.value,
                },
                { abortEarly: false }
            );

            registerUser.mutate(
                {
                    token: emailToken.token,
                    first_name: firstName,
                    second_name: secondName,
                    password: encodeToBase64(password.value),
                },
                {
                    onSuccess: () => {
                        redirectTo(paths.root({}));
                    },
                }
            );
        } catch (error: unknown) {
            if (isYupValidationError(error)) {
                error.inner.forEach(({ path, message }: ValidationError) => {
                    if (path === 'password') {
                        setPassword(handleErrorMessageState(message));
                    } else if (path === 'confirmPassword') {
                        setConfirmPassword(handleErrorMessageState(message));
                    }
                });
            }
        }
    };

    const dismiss = () => {
        // We don't allow the user to dismiss this modal, they need to finish the registration
        // before they are allowed to use Geti
    };

    return (
        <View UNSAFE_className={classes.termsAndConditionsBg}>
            <DialogContainer onDismiss={dismiss} isDismissable={false} isKeyboardDismissDisabled>
                <Dialog UNSAFE_className={classes.dialog}>
                    <Heading UNSAFE_className={classes.dialogHeader}>
                        <Text>{`Let's complete your registration!`}</Text>
                    </Heading>
                    <Content UNSAFE_className={classes.content}>
                        <Form onSubmit={handleSubmit}>
                            <Flex
                                direction={'column'}
                                UNSAFE_style={{
                                    padding: 'size-300',
                                    paddingTop: 0,
                                }}
                            >
                                <Heading level={6} marginBottom={'size-300'}>
                                    Please provide the following details.
                                </Heading>

                                <Flex direction={'column'}>
                                    <TextField
                                        // eslint-disable-next-line jsx-a11y/no-autofocus
                                        autoFocus
                                        label='First name'
                                        id='edit-first-name'
                                        width='100%'
                                        value={firstName}
                                        onChange={setFirstName}
                                        isDisabled={emailTokenIsInvalid}
                                    />
                                    <TextField
                                        label='Last name'
                                        id='edit-last-name'
                                        marginTop={'size-200'}
                                        width='100%'
                                        value={secondName}
                                        onChange={setSecondName}
                                        isDisabled={emailTokenIsInvalid}
                                    />
                                    <PasswordField
                                        id={'password-id'}
                                        error={password.error}
                                        label={'Password'}
                                        marginTop={'size-200'}
                                        value={password.value}
                                        onChange={handlePassword}
                                        autoComplete='off'
                                        isDisabled={emailTokenIsInvalid}
                                        isNewPassword
                                    />
                                    <PasswordField
                                        id={'confirm-password-id'}
                                        error={confirmPassword.error}
                                        label={'Confirm password'}
                                        value={confirmPassword.value}
                                        onChange={handleConfirmPassword}
                                        autoComplete='off'
                                        isDisabled={emailTokenIsInvalid}
                                    />
                                </Flex>
                            </Flex>
                            <InvalidTokenAlert
                                isVisible={emailTokenIsInvalid}
                                message={emailToken.token === null ? emailToken.error : ''}
                                styles={{ marginBottom: 'size-200' }}
                            />
                            <ButtonGroup width={'100%'} align={'end'}>
                                <Button
                                    type='submit'
                                    variant={'accent'}
                                    id={'submit-button'}
                                    isDisabled={isBtnDisabled}
                                >
                                    Sign up
                                </Button>
                            </ButtonGroup>
                        </Form>
                    </Content>
                </Dialog>
            </DialogContainer>
        </View>
    );
};
