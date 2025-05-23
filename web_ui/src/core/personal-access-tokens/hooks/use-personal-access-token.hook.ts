// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useMutation, useQuery, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import QUERY_KEYS from '../../requests/query-keys';
import {
    BaseTokenProps,
    CreatePersonalAccessTokenPayload,
    DeletePersonalAccessTokenPayload,
    PartialPersonalAccessToken,
    PersonalAccessToken,
    PersonalAccessTokens,
    UpdatePersonalAccessTokenPayload,
    UsePersonalAccessToken,
} from '../personal-access-tokens.interface';

export const DELETE_MESSAGE = 'Personal Access Token was not deleted due to an error.';
export const RETRIEVE_ERROR = 'Personal Access Token was not retrieved due to an error.';
export const UPDATE_MESSAGE = 'The expiration date has been updated.';

export const usePersonalAccessToken = (): UsePersonalAccessToken => {
    const queryClient = useQueryClient();
    const { personalAccessTokensService } = useApplicationServices();
    const { addNotification } = useNotification();

    const createPersonalAccessTokenMutation = useMutation<
        PersonalAccessToken,
        AxiosError,
        CreatePersonalAccessTokenPayload
    >({
        mutationFn: (props: CreatePersonalAccessTokenPayload) =>
            personalAccessTokensService.createPersonalAccessToken(props),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: QUERY_KEYS.SERVICE_ACCOUNTS_API_KEY });
        },
        onError: (error: AxiosError) => {
            const message = error?.message ?? RETRIEVE_ERROR;
            addNotification({ message, type: NOTIFICATION_TYPE.ERROR });
        },
    });

    const deletePersonalAccessTokenMutation = useMutation<void, AxiosError, DeletePersonalAccessTokenPayload>({
        mutationFn: (props: DeletePersonalAccessTokenPayload) =>
            personalAccessTokensService.deletePersonalAccessToken(props),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: QUERY_KEYS.SERVICE_ACCOUNTS_API_KEY });
        },
        onError: (error: AxiosError) => {
            const message = error?.message ?? DELETE_MESSAGE;
            addNotification({ message, type: NOTIFICATION_TYPE.ERROR });
        },
    });

    const updatePersonalAccessTokenMutation = useMutation<
        PartialPersonalAccessToken,
        AxiosError,
        UpdatePersonalAccessTokenPayload
    >({
        mutationFn: (props: UpdatePersonalAccessTokenPayload) =>
            personalAccessTokensService.updatePersonalAccessToken(props),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: QUERY_KEYS.SERVICE_ACCOUNTS_API_KEY });
            addNotification({ message: UPDATE_MESSAGE, type: NOTIFICATION_TYPE.DEFAULT });
        },
        onError: (error: AxiosError) => {
            const message = error?.message ?? DELETE_MESSAGE;
            addNotification({ message, type: NOTIFICATION_TYPE.ERROR });
        },
    });

    const useGetPersonalAccessTokensQuery = (props: BaseTokenProps): UseQueryResult<PersonalAccessTokens, AxiosError> =>
        useQuery<PersonalAccessTokens, AxiosError>({
            queryKey: QUERY_KEYS.SERVICE_ACCOUNTS_API_KEY,
            queryFn: async () => await personalAccessTokensService.getPersonalAccessTokens(props),
            retry: 1,
        });

    return {
        createPersonalAccessTokenMutation,
        useGetPersonalAccessTokensQuery,
        deletePersonalAccessTokenMutation,
        updatePersonalAccessTokenMutation,
    };
};
