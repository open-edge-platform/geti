// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { AlertDialog } from '@adobe/react-spectrum';
import { useQueryClient } from '@tanstack/react-query';
import isFunction from 'lodash/isFunction';

import QUERY_KEYS from '../../../../../core/requests/query-keys';
import { useUsers } from '../../../../../core/users/hook/use-users.hook';
import { User } from '../../../../../core/users/users.interface';
import { useHandleSignOut } from '../../../../../hooks/use-handle-sign-out/use-handle-sign-out.hook';

import classes from '../workspace-user.module.scss';

interface UserActionsProps {
    organizationId: string;
    user: User;
    activeUser: User | undefined;
    onDeleting?: () => void;
}
export const RemoveUserDialog = ({ organizationId, user, activeUser, onDeleting }: UserActionsProps): JSX.Element => {
    const handleSignOut = useHandleSignOut();
    const { useDeleteUser } = useUsers();
    const deleteUser = useDeleteUser();

    const queryClient = useQueryClient();
    const deleteUserAction = async () => {
        // mutation `onSuccess` wasn't called always even when the endpoint return (200 OK)
        // This is a quick fix and requires more investigation
        // https://stackoverflow.com/questions/70217129/react-query-usemutation-is-putting-my-api-call-state-in-idle
        try {
            isFunction(onDeleting) && onDeleting();

            await deleteUser.mutateAsync({ organizationId, user });
            await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });

            if (activeUser?.id === user.id) {
                handleSignOut();
            }
        } catch (_error: unknown) {}
    };

    const question = `Are you sure you want to delete "${user.email}"?`;

    return (
        <AlertDialog
            title='Delete'
            variant='destructive'
            primaryActionLabel='Delete'
            onPrimaryAction={deleteUserAction}
            cancelLabel={'Cancel'}
            UNSAFE_className={classes.removeUserDialog}
        >
            {question}
        </AlertDialog>
    );
};
