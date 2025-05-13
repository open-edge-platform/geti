// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AlertDialog } from '@adobe/react-spectrum';
import { useQueryClient } from '@tanstack/react-query';
import { isFunction } from 'lodash-es';

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
