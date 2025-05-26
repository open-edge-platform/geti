// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FormEvent, useRef, useState } from 'react';

import QUERY_KEYS from '@geti/core/src/requests/query-keys';
import { useUsers } from '@geti/core/src/users/hook/use-users.hook';
import { User } from '@geti/core/src/users/users.interface';
import { Button, Flex, Form, TextField, View } from '@geti/ui';
import { useQueryClient } from '@tanstack/react-query';

import { useHistoryBlock } from '../../../hooks/use-history-block/use-history-block.hook';
import { UnsavedChangesDialog } from '../../../shared/components/unsaved-changes-dialog/unsaved-changes-dialog.component';
import { getFullNameFromUser } from '../users/users-table/utils';
import { DisplayFullName } from './display-full-name.component';
import { EditFullName } from './edit-full-name.component';
import { UserPhotoContainer } from './user-photo-container/user-photo-container.component';

import classes from './profile-page.module.scss';

interface ProfilePageProps {
    activeUser: User;
    organizationId: string;
    isSaaSEnv: boolean;
}

export const ProfilePage = ({ activeUser, organizationId, isSaaSEnv }: ProfilePageProps): JSX.Element => {
    const { useUpdateUser } = useUsers();
    const updateUser = useUpdateUser();
    const queryClient = useQueryClient();

    const prevFirstName = useRef<string>(activeUser.firstName);
    const prevLastName = useRef<string>(activeUser.lastName);

    const [firstName, setFirstName] = useState<string>(activeUser.firstName);
    const [lastName, setLastName] = useState<string>(activeUser.lastName);

    const [open, setOpen, onUnsavedAction] = useHistoryBlock(
        prevFirstName.current !== firstName || prevLastName.current !== lastName
    );

    const isDisabled = prevFirstName.current === firstName && prevLastName.current === lastName;

    const onSubmit = (event: FormEvent): void => {
        event.preventDefault();

        const editedUser: User = {
            ...activeUser,
            firstName,
            lastName,
        };

        updateUser.mutate(
            { user: editedUser, userId: activeUser.id, organizationId },
            {
                onSuccess: async () => {
                    prevFirstName.current = firstName;
                    prevLastName.current = lastName;
                    await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ACTIVE_USER(organizationId) });
                    await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });
                },
            }
        );
    };

    return (
        <>
            <View position={'relative'} height={'100%'}>
                <Form onSubmit={onSubmit}>
                    <Flex direction='column'>
                        <UserPhotoContainer
                            userId={activeUser.id}
                            userName={getFullNameFromUser(activeUser)}
                            userPhoto={activeUser.userPhoto}
                            email={activeUser.email}
                        />
                        <TextField
                            type='text'
                            id='email-id'
                            label='Email address'
                            value={activeUser.email}
                            isReadOnly
                            UNSAFE_className={[classes.textFieldReadOnly, classes.textField].join(' ')}
                            marginBottom='size-175'
                        />

                        {isSaaSEnv ? (
                            <DisplayFullName firstName={firstName} lastName={lastName} />
                        ) : (
                            <>
                                <EditFullName
                                    cssClass={classes.textFieldSmaller}
                                    firstName={firstName}
                                    setFirstName={setFirstName}
                                    lastName={lastName}
                                    setLastName={setLastName}
                                    isQuiet
                                    marginBottom={'size-550'}
                                />
                                <Button
                                    variant='accent'
                                    id='save-btn'
                                    alignSelf='flex-start'
                                    type='submit'
                                    marginBottom='size-550'
                                    isDisabled={isDisabled}
                                    isPending={updateUser.isPending}
                                >
                                    Save
                                </Button>
                            </>
                        )}
                    </Flex>
                </Form>
            </View>
            <UnsavedChangesDialog open={open} setOpen={setOpen} onPrimaryAction={onUnsavedAction} />
        </>
    );
};
