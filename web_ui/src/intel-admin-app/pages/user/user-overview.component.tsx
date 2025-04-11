// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC, useState } from 'react';

import { Divider, Flex, Text, TextField, View } from '@adobe/react-spectrum';

import { Delete } from '../../../assets/icons';
import { ActionButton } from '../../../shared/components/button/button.component';
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
