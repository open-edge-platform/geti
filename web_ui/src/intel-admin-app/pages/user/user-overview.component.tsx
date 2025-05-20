// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { ActionButton, Divider, Flex, Text, TextField, View } from '@geti/ui';
import { Delete } from '@geti/ui/icons';

import { Header } from '../../shared/components/header/header.component';
import { MOCKED_USERS, User } from '../users/mocked-user';
import { DeleteUserDialog } from '../users/user-actions/delete-user-dialog.component';

import classes from './user-overview.module.scss';

interface DeleteUserProps {
    user: User;
}

const DeleteUser: FC<DeleteUserProps> = ({ user }) => {
    const [isDeleteDialogVisible, setIsDeleteDialogVisible] = useState<boolean>(false);

    const handleOpenDeleteDialog = (): void => {
        setIsDeleteDialogVisible(true);
    };

    const handleCancel = (): void => {
        setIsDeleteDialogVisible(false);
    };

    return (
        <>
            <ActionButton UNSAFE_className={classes.deleteButton} onPress={handleOpenDeleteDialog}>
                <Flex>
                    <Delete />
                </Flex>
                <Text>Delete</Text>
            </ActionButton>
            <DeleteUserDialog
                name={`${user.firstName} ${user.secondName}`}
                onCancel={handleCancel}
                isOpen={isDeleteDialogVisible}
            />
        </>
    );
};

const [user] = MOCKED_USERS;

export const UserOverview: FC = () => {
    return (
        <>
            <Header title={'Overview'} />
            <View>
                <Flex direction={'column'} gap={'size-250'}>
                    <TextField
                        label='Email address'
                        defaultValue={user.email}
                        width='size-3000'
                        isReadOnly
                        isQuiet
                        UNSAFE_className={classes.emailFieldReadOnly}
                    />
                    <TextField
                        label='First name'
                        defaultValue={user.firstName}
                        width='size-3000'
                        isReadOnly
                        isQuiet
                        UNSAFE_className={classes.emailFieldReadOnly}
                    />
                    <TextField
                        label='Last name'
                        defaultValue={user.secondName}
                        width='size-3000'
                        isReadOnly
                        isQuiet
                        UNSAFE_className={classes.emailFieldReadOnly}
                    />
                </Flex>
                <Divider size={'S'} marginY={'size-300'} />
                <DeleteUser user={user} />
            </View>
        </>
    );
};
