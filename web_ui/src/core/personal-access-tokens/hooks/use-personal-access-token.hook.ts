// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useMutation, useQuery, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
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
