// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useMemo } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useInfiniteQuery, useMutation, UseMutationResult, useQuery, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { StatusCodes } from 'http-status-codes';
import { validate } from 'uuid';

import { paths } from '../../../../packages/core/src/services/routes';
import { getErrorMessage } from '../../../../packages/core/src/services/utils';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { redirectTo } from '../../../shared/utils';
import { AccountStatusDTO } from '../../organizations/dtos/organizations.interface';
import QUERY_KEYS from '../../requests/query-keys';
import { ForgotPasswordDTO, ResetPasswordDTO, UpdatePasswordDTO, UserRegistrationDTO } from '../dtos/members.interface';
import { getUsersQueryParamsDTO } from '../services/utils';
import { RoleResource, User, UsersResponse } from '../users.interface';
import {
    UseCreateUserPayload,
    UseDeleteUserPayload,
    UseDeleteUserPhotoPayload,
    UseInviteUserPayload,
    UseUpdateUserPayload,
    UseUpdateUserStatusesPayload,
    UseUploadUserPhotoPayload,
    UseUsers,
} from './use-users.interface';

export const useForgotPassword = (): UseMutationResult<void, AxiosError, ForgotPasswordDTO> => {
    const { usersService } = useApplicationServices();

    return useMutation<void, AxiosError, ForgotPasswordDTO>({
        mutationFn: usersService.forgotPassword,
        meta: {
            notifyOnError: true,
        },
    });
};

export const useResetPassword = (): UseMutationResult<void, AxiosError, ResetPasswordDTO> => {
    const { usersService } = useApplicationServices();

    return useMutation({
        mutationFn: async (body: ResetPasswordDTO) => {
            await usersService.resetPassword(body);
        },

        meta: {
            notifyOnError: true,
        },
        onSuccess: () => redirectTo(paths.root({})),
    });
};

export const useChangePassword = (): UseMutationResult<void, AxiosError, UpdatePasswordDTO> => {
    const { usersService } = useApplicationServices();

    return useMutation<void, AxiosError, UpdatePasswordDTO>({
        mutationFn: usersService.updatePassword,
        meta: {
            notifyOnError: true,
        },
    });
};

export const useUserRegister = (): UseMutationResult<void, AxiosError, UserRegistrationDTO> => {
    const { usersService } = useApplicationServices();
    const { addNotification } = useNotification();

    const handleError = (error: AxiosError) => {
        addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
    };

    const handleUserNotFoundError = () => {
        addNotification({
            message: 'User does not exist, it may have been deleted by the administrator.',
            type: NOTIFICATION_TYPE.ERROR,
        });
    };

    return useMutation({
        mutationFn: async (body: UserRegistrationDTO) => {
            await usersService.registerMember(body);
        },

        onError: (error: AxiosError) => {
            if (error.status === StatusCodes.NOT_FOUND) {
                handleUserNotFoundError();
            } else {
                handleError(error);
            }
        },

        onSuccess: () => redirectTo(paths.root({})),
    });
};

export const useUsers = (): UseUsers => {
    const { usersService } = useApplicationServices();

    const { addNotification } = useNotification();
    const queryClient = useQueryClient();

    const useGetUsersQuery: UseUsers['useGetUsersQuery'] = (organizationId, queryParams = {}) => {
        const { data, isPending, isSuccess, isError, hasNextPage, isFetchingNextPage, fetchNextPage } =
            useInfiniteQuery<UsersResponse, AxiosError>({
                queryKey: QUERY_KEYS.USERS(organizationId, queryParams),
                queryFn: ({ pageParam: nextPage = null }) => {
                    const nextPageParams = nextPage !== null ? { ...nextPage } : {};

                    return usersService.getUsers(
                        organizationId,
                        getUsersQueryParamsDTO({ ...queryParams, ...nextPageParams })
                    );
                },
                meta: { notifyOnError: true },
                getNextPageParam: ({ nextPage, totalCount }) => {
                    if (nextPage === null) {
                        return undefined;
                    }

                    return totalCount > nextPage.skip ? nextPage : undefined;
                },
                getPreviousPageParam: () => undefined,
                initialPageParam: undefined,
            });

        const users = useMemo(() => {
            return data?.pages.flatMap((page) => page.users) ?? [];
        }, [data?.pages]);
        const totalCount = data?.pages.at(0)?.totalCount ?? 0;
        const totalMatchedCount = data?.pages.at(0)?.totalMatchedCount ?? 0;

        const getNextPage = async (): Promise<void> => {
            if (hasNextPage && !isFetchingNextPage) {
                await fetchNextPage();
            }
        };

        return {
            users,
            isLoading: isPending,
            isSuccess,
            isError,
            totalCount,
            totalMatchedCount,
            getNextPage,
            isFetchingNextPage,
        };
    };

    const useGetUserQuery: UseUsers['useGetUserQuery'] = (organizationId, userId) => {
        return useQuery<User, AxiosError>({
            queryKey: QUERY_KEYS.USER(organizationId, userId),
            queryFn: () => {
                if (userId === undefined) {
                    throw new Error('Undefined userId');
                }

                // This handles the edge case where we get the user id as "user@intel.com".
                // This happens when the uploader/annotator id no longer exists so the backend
                // replaces the uploader/annotator id for "user@intel.com".
                // If the user id is not a uuid and we request a user via the account service that we then get
                // a 200 response with the html document of the web ui as its response.
                // TODO: update this after both tickets are resolved
                if (!validate(userId)) {
                    throw new Error('Invalid userId');
                }

                return usersService.getUser(organizationId, userId);
            },
            enabled: userId !== undefined && validate(userId),
            // We set a relatively high stale and cache time to prevent too many
            // API calls from being made.
            staleTime: 60 * 60 * 5,
            gcTime: 60 * 60 * 10,

            // Prevent us from showing a 403 modal
            meta: {
                disableGlobalErrorHandling: true,
            },
        });
    };

    const useInviteUserMutation: UseUsers['useInviteUserMutation'] = () =>
        useMutation<void, AxiosError, UseInviteUserPayload>({
            mutationFn: ({ organizationId, email, roles }) => usersService.inviteUser(organizationId, email, roles),
            onSuccess: async (_, { organizationId, email }) => {
                addNotification({ message: `The invite has been sent to: ${email}`, type: NOTIFICATION_TYPE.DEFAULT });
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });
            },
            onError: (error: AxiosError) => {
                addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
            },
        });

    const useCreateUser: UseUsers['useCreateUser'] = () => {
        return useMutation<User, AxiosError, UseCreateUserPayload>({
            mutationFn: ({ user, organizationId }) => {
                return usersService.createUser(organizationId, user);
            },
            onSuccess: async (_, { organizationId }) => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });
            },
        });
    };

    const useUpdateUser: UseUsers['useUpdateUser'] = () => {
        return useMutation<User, AxiosError, UseUpdateUserPayload>({
            mutationFn: ({ user, organizationId }) => {
                return usersService.updateUser(organizationId, user);
            },
            onSuccess: async (_, { organizationId }) => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ACTIVE_USER(organizationId) });
            },
        });
    };

    const useUpdateUserStatuses: UseUsers['useUpdateUserStatuses'] = () => {
        return useMutation<void, AxiosError, UseUpdateUserStatusesPayload>({
            mutationFn: ({ userId, organizationId, status }) => {
                return usersService.updateUserStatuses(organizationId, userId, status);
            },
            onSuccess: async (_, { organizationId }) => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ACTIVE_USER(organizationId) });
            },
        });
    };

    const useDeleteUser: UseUsers['useDeleteUser'] = () => {
        return useMutation<void, AxiosError, UseDeleteUserPayload>({
            mutationFn: ({ organizationId, user }) => {
                return usersService.updateUserStatuses(organizationId, user.id, AccountStatusDTO.DELETED);
            },
            onSuccess: async (_, { organizationId }) => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });
            },
        });
    };

    const useUploadUserPhoto: UseUsers['useUploadUserPhoto'] = () => {
        return useMutation<void, AxiosError, UseUploadUserPhotoPayload>({
            mutationFn: ({ organizationId, userId, userPhoto }) => {
                return usersService.uploadUserPhoto(organizationId, userId, userPhoto);
            },
            onSuccess: async (_, { organizationId }) => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ACTIVE_USER(organizationId) });
            },
        });
    };

    const useDeleteUserPhoto: UseUsers['useDeleteUserPhoto'] = () => {
        return useMutation<void, AxiosError, UseDeleteUserPhotoPayload>({
            mutationFn: ({ organizationId, userId }) => {
                return usersService.deleteUserPhoto(organizationId, userId);
            },
            onSuccess: async (_, { organizationId }) => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });
            },
        });
    };

    const useUserRoles: UseUsers['useUserRoles'] = ({ organizationId, userId, resourceType }) => {
        const query = useQuery<RoleResource[], AxiosError>({
            queryKey: QUERY_KEYS.USER_ROLES(organizationId, userId, resourceType),
            queryFn: () => {
                return usersService.getRoles(organizationId, userId, resourceType);
            },
        });

        useEffect(() => {
            if (!query.isSuccess) {
                return;
            }

            queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });
        }, [query.isSuccess, query.data, organizationId]);

        return query;
    };

    const useActiveUser: UseUsers['useActiveUser'] = (organizationId) => {
        const key = QUERY_KEYS.ACTIVE_USER(organizationId);

        return useQuery<User, AxiosError>({
            queryKey: key,
            queryFn: () => {
                return usersService.getActiveUser(organizationId);
            },
        });
    };

    const useUpdateUserRoles: UseUsers['useUpdateUserRoles'] = () => {
        return useMutation({
            mutationFn: async ({ organizationId, userId, newRoles }) => {
                return usersService.updateRoles(organizationId, userId, newRoles);
            },
            onSuccess: (_, { organizationId, userId }) => {
                queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });
                queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USER_ROLES(organizationId, userId) });
            },
        });
    };

    const useUpdateMemberRole: UseUsers['useUpdateMemberRole'] = () => {
        return useMutation({
            mutationFn: async ({ organizationId, memberId, role }) => {
                await usersService.updateMemberRole(organizationId, memberId, role);
            },
            onSuccess: (_, { organizationId }) => {
                queryClient.invalidateQueries({ queryKey: QUERY_KEYS.USERS(organizationId) });
                queryClient.invalidateQueries({ queryKey: QUERY_KEYS.ACTIVE_USER(organizationId) });
            },
        });
    };

    const useDeleteMemberRole: UseUsers['useDeleteMemberRole'] = () => {
        return useMutation({
            mutationFn: async ({ organizationId, memberId, role }) => {
                await usersService.deleteMemberRole(organizationId, memberId, role);
            },
        });
    };

    return {
        useActiveUser,
        useGetUsersQuery,
        useGetUserQuery,
        useInviteUserMutation,
        useCreateUser,
        useUpdateUser,
        useUpdateUserStatuses,
        useUpdateUserRoles,
        useDeleteUser,
        useUploadUserPhoto,
        useDeleteUserPhoto,
        useUserRoles,

        useUpdateMemberRole,
        useDeleteMemberRole,
    };
};
