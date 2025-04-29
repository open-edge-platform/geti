// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { instance as defaultAxiosInstance } from '../services/axios-instance';
import { CreateApiService } from '../services/create-api-service.interface';
import { API_URLS } from '../services/urls';
import {
    BaseTokenProps,
    CreatePersonalAccessTokenPayload,
    DeletePersonalAccessTokenPayload,
    PartialPersonalAccessToken,
    PersonalAccessToken,
    PersonalAccessTokens,
    PersonalAccessTokensService,
    UpdatePersonalAccessTokenPayload,
} from './personal-access-tokens.interface';

export const createApiPersonalAccessTokensService: CreateApiService<PersonalAccessTokensService> = (
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
) => {
    const createPersonalAccessToken = async (props: CreatePersonalAccessTokenPayload): Promise<PersonalAccessToken> => {
        const { data } = await instance.post<PersonalAccessToken>(
            router.PERSONAL_ACCESS_TOKENS(props.organizationId, props.userId),
            {
                expiresAt: props.expirationDate,
                name: props.name,
                description: props.description,
            }
        );
        return data;
    };

    const getPersonalAccessTokens = async (props: BaseTokenProps): Promise<PersonalAccessTokens> => {
        const { data } = await instance.get<PersonalAccessTokens>(
            router.PERSONAL_ACCESS_TOKENS(props.organizationId, props.userId)
        );

        return data;
    };

    const deletePersonalAccessToken = async (props: DeletePersonalAccessTokenPayload): Promise<void> => {
        return instance.delete(router.PERSONAL_ACCESS_TOKEN(props.organizationId, props.userId, props.tokenId));
    };

    const updatePersonalAccessToken = async (
        props: UpdatePersonalAccessTokenPayload
    ): Promise<PartialPersonalAccessToken> => {
        return instance.patch(router.PERSONAL_ACCESS_TOKEN(props.organizationId, props.userId, props.tokenId), {
            expiresAt: props.expirationDate,
        });
    };

    return {
        getPersonalAccessTokens,
        createPersonalAccessToken,
        deletePersonalAccessToken,
        updatePersonalAccessToken,
    };
};
