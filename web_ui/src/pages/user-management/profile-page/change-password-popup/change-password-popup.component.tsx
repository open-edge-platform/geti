// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FormEvent, useState } from 'react';

import { Button, ButtonGroup, Content, Dialog, DialogTrigger, Divider, Form, Heading, PasswordField } from '@geti/ui';
import { ValidationError } from 'yup';

import { useChangePassword } from '../../../../core/users/hook/use-users.hook';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { ColorMode, QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { CONFIRM_PASSWORD_ERROR_MESSAGE, encodeToBase64 } from '../../../../shared/utils';
import { PasswordState } from '../../users/add-member-popup/add-member-popup.interface';
import { handlePassword } from '../../users/add-member-popup/utils';
import { isYupValidationError } from '../utils';
import { defaultPassword, ErrorUserManagementMessages, passwordSchema } from './utils';

import classes from './change-password-popup.module.scss';

enum ErrorPath {
    OLD_PASSWORD = 'oldPassword',
    NEW_PASSWORD = 'newPassword',
    CONFIRM_PASSWORD = 'confirmPassword',
}

interface ChangePasswordPopupProps {
    userId: string;
}

export const ChangePasswordPopup = ({ userId }: ChangePasswordPopupProps): JSX.Element => {
    const [oldPassword, setOldPassword] = useState<PasswordState>(defaultPassword);
    const [newPassword, setNewPassword] = useState<PasswordState>(defaultPassword);
    const [confirmPassword, setConfirmPassword] = useState<PasswordState>(defaultPassword);

    const changePassword = useChangePassword();
    const { addNotification } = useNotification();

    const isDisabled = Boolean(
        !oldPassword.value ||
            !newPassword.value ||
            !confirmPassword.value ||
            oldPassword.error ||
            newPassword.error ||
            confirmPassword.error
    );

    const clearFields = (): void => {
        if (oldPassword.value || oldPassword.error) {
            setOldPassword(defaultPassword);
        }
        if (newPassword.value || newPassword.error) {
            setNewPassword(defaultPassword);
        }
        if (confirmPassword.value || newPassword.error) {
            setConfirmPassword(defaultPassword);
        }
    };

    const handleChangePassword = (close: () => void) => {
        return async (event: FormEvent): Promise<void> => {
            event.preventDefault();

            try {
                const result = passwordSchema.validateSync(
                    {
                        oldPassword: oldPassword.value,
                        newPassword: newPassword.value,
                        confirmPassword: confirmPassword.value,
                    },
                    { abortEarly: false }
                );
                changePassword.mutate(
                    {
                        uid: userId,
                        old_password: encodeToBase64(result.oldPassword),
                        new_password: encodeToBase64(result.newPassword),
                    },
                    {
                        onSuccess: () => {
                            close();
                            clearFields();
                            addNotification({
                                message: 'Password changed successfully',
                                type: NOTIFICATION_TYPE.DEFAULT,
                            });
                        },
                        onError: (error) => {
                            if (error.message.includes(ErrorUserManagementMessages.SAME_NEW_PASSWORD)) {
                                setNewPassword((prevPassword) => ({
                                    ...prevPassword,
                                    error: ErrorUserManagementMessages.SAME_NEW_PASSWORD,
                                }));
                            } else if (error.message.includes(ErrorUserManagementMessages.WRONG_OLD_PASSWORD)) {
                                setOldPassword((prevPassword) => ({
                                    ...prevPassword,
                                    error: ErrorUserManagementMessages.WRONG_OLD_PASSWORD,
                                }));
                            } else {
                                addNotification({ message: error.message, type: NOTIFICATION_TYPE.ERROR });
                            }
                        },
                    }
                );
            } catch (error: unknown) {
                const errorMsgs = {
                    oldPassword: new Array<string>(),
                    newPassword: new Array<string>(),
                    confirmPassword: new Array<string>(),
                };
                if (isYupValidationError(error)) {
                    error.inner.forEach(({ path, message }: ValidationError) => {
                        if (path === ErrorPath.OLD_PASSWORD) {
                            errorMsgs.oldPassword.push(message);
                        } else if (path === ErrorPath.NEW_PASSWORD) {
                            errorMsgs.newPassword.push(message);
                        } else if (path === ErrorPath.CONFIRM_PASSWORD) {
                            errorMsgs.confirmPassword.push(CONFIRM_PASSWORD_ERROR_MESSAGE);
                        }
                    });

                    if (errorMsgs.oldPassword.length) {
                        setOldPassword((prev: PasswordState) => ({
                            ...prev,
                            error: errorMsgs.oldPassword[0],
                        }));
                    }
                    if (errorMsgs.newPassword.length) {
                        setNewPassword((prev: PasswordState) => ({
                            ...prev,
                            error: errorMsgs.newPassword[0],
                        }));
                    }
                    if (errorMsgs.confirmPassword.length) {
                        setConfirmPassword((prev: PasswordState) => ({
                            ...prev,
                            error: errorMsgs.confirmPassword[0],
                        }));
                    }
                }
            }
        };
    };

    return (
        <DialogTrigger>
            <QuietActionButton colorMode={ColorMode.BLUE} alignSelf='self-start' id={'change-password-button'}>
                Change password
            </QuietActionButton>
            {(close) => (
                <Dialog UNSAFE_className={classes.popupBox}>
                    <Heading UNSAFE_className={classes.popupTitle}>Change password</Heading>
                    <Divider />
                    <Content>
                        <Form onSubmit={handleChangePassword(close)}>
                            <PasswordField
                                id='old-password'
                                label='Old password'
                                // eslint-disable-next-line jsx-a11y/no-autofocus
                                autoFocus
                                value={oldPassword.value}
                                error={oldPassword.error}
                                autoComplete='off'
                                onChange={handlePassword(setOldPassword)}
                            />
                            <PasswordField
                                id='new-password'
                                label='New password'
                                value={newPassword.value}
                                error={newPassword.error}
                                autoComplete='off'
                                onChange={handlePassword(setNewPassword)}
                                isNewPassword
                            />
                            <PasswordField
                                id='confirm-password'
                                label='Confirm new password'
                                value={confirmPassword.value}
                                error={confirmPassword.error}
                                autoComplete='off'
                                onChange={handlePassword(setConfirmPassword)}
                            />
                            <ButtonGroup align={'end'} marginTop={'size-350'}>
                                <Button
                                    variant='secondary'
                                    id='cancel-popup-btn'
                                    onPress={() => {
                                        close();
                                        clearFields();
                                    }}
                                >
                                    Cancel
                                </Button>
                                <Button
                                    id='save-popup-btn'
                                    type='submit'
                                    isPending={changePassword.isPending}
                                    isDisabled={isDisabled}
                                >
                                    Save
                                </Button>
                            </ButtonGroup>
                        </Form>
                    </Content>
                </Dialog>
            )}
        </DialogTrigger>
    );
};
