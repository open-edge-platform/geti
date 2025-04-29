// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AlertDialog } from '@adobe/react-spectrum';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import QUERY_KEYS from '../../../../core/requests/query-keys';
import { paths } from '../../../../core/services/routes';
import { useUsers } from '../../../../core/users/hook/use-users.hook';
import { getRoleDeletionPayload } from '../../../../core/users/services/utils';
import { RESOURCE_TYPE, User } from '../../../../core/users/users.interface';
import { useProjectIdentifier } from '../../../../hooks/use-project-identifier/use-project-identifier';

interface UserActionsProps {
    user: User;
    activeUser: User | undefined;
    dismiss: () => void;
}

export const RemoveUserFromProjectDialog = ({ user, activeUser, dismiss }: UserActionsProps): JSX.Element => {
    const { FEATURE_FLAG_MANAGE_USERS_ROLES } = useFeatureFlags();
    const { useUpdateUserRoles, useDeleteMemberRole } = useUsers();
    const { organizationId, workspaceId, projectId } = useProjectIdentifier();
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    const setUserRoleMutation = useUpdateUserRoles();
    const deleteMemberRole = useDeleteMemberRole();

    const deleteMemberAction = async () => {
        const projectRole = user.roles.find(
            (role) => role.resourceId === projectId && role.resourceType === RESOURCE_TYPE.PROJECT
        );

        if (projectRole === undefined) {
            return;
        }

        deleteMemberRole.mutate(
            {
                organizationId,
                memberId: user.id,
                role: {
                    role: projectRole.role,
                    resourceId: projectRole.resourceId,
                },
            },
            {
                onSuccess: async () => {
                    // If the current user was removed from the project, redirect to home
                    // and refresh the project list
                    if (activeUser?.id === user.id && !user.isAdmin) {
                        // Since the user is removed from the project, we immediately
                        // want to remove the cached projects query
                        queryClient.removeQueries({ queryKey: QUERY_KEYS.PROJECTS_KEY(workspaceId) });

                        navigate(paths.home({ organizationId, workspaceId }), { replace: true });
                    } else {
                        await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });
                    }
                },
            }
        );
    };

    const deleteUserAction = async () => {
        setUserRoleMutation.mutate(
            {
                organizationId,
                newRoles: user.roles
                    .filter((role) => role.resourceId === projectId && role.resourceType === RESOURCE_TYPE.PROJECT)
                    .map((role) => getRoleDeletionPayload(role)),
                userId: user.id,
            },
            {
                onSuccess: async () => {
                    // If the current user was removed from the project, redirect to home
                    // and refresh the project list
                    if (activeUser?.id === user.id && !user.isAdmin) {
                        // Since the user is removed from the project, we immediately
                        // want to remove the cached projects query
                        queryClient.removeQueries({ queryKey: QUERY_KEYS.PROJECTS_KEY(workspaceId) });

                        navigate(paths.home({ organizationId, workspaceId }), { replace: true });
                    } else {
                        await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });
                    }
                },
            }
        );
    };

    const question = `Are you sure you want to remove "${user.email}" from the project?`;

    return (
        <AlertDialog
            title='Delete'
            variant='destructive'
            primaryActionLabel='Delete'
            onPrimaryAction={FEATURE_FLAG_MANAGE_USERS_ROLES ? deleteMemberAction : deleteUserAction}
            cancelLabel={'Cancel'}
            onCancel={dismiss}
        >
            {question}
        </AlertDialog>
    );
};
