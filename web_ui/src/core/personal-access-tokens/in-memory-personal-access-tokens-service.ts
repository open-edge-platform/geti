// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    CreatePersonalAccessTokenPayload,
    PartialPersonalAccessToken,
    PersonalAccessToken,
    PersonalAccessTokens,
    PersonalAccessTokensService,
} from './personal-access-tokens.interface';

export const createInMemoryPersonalAccessTokensService = (): PersonalAccessTokensService => {
    const createPersonalAccessToken = async (
        _props: CreatePersonalAccessTokenPayload
    ): Promise<PersonalAccessToken> => {
        return Promise.resolve({
            id: '4a5f12e2-2bbb-435a-910b-28949f739650',
            partial: 'geti_pat_dNSBPdJ1Y9S',
            name: 'name',
            description: 'description',
            expiresAt: '2024-06-20T11:11:11.062Z',
            organizationId: 'de61b273-a8cf-4dd7-96a4-b5e1c5b131fd',
            userId: 'b82da6f8-5352-4dbb-99d7-84135a811bea',
            createdAt: '2024-02-08T12:17:26Z',
            personalAccessToken: 'JRR Token',
        });
    };

    const getPersonalAccessTokens = async (): Promise<PersonalAccessTokens> => {
        return Promise.resolve({
            personalAccessTokens: [
                {
                    id: '4a5f12e2-2bbb-435a-910b-28949f739650',
                    partial: 'geti_pat_dNSBPdJ1Y9S',
                    name: 'name',
                    description: 'description',
                    expiresAt: '2024-06-20T11:11:11.062Z',
                    organizationId: 'de61b273-a8cf-4dd7-96a4-b5e1c5b131fd',
                    userId: 'b82da6f8-5352-4dbb-99d7-84135a811bea',
                    createdAt: '2024-02-08T12:17:26Z',
                },
            ],
        });
    };

    const deletePersonalAccessToken = async (): Promise<void> => {
        return Promise.resolve();
    };

    const updatePersonalAccessToken = async (): Promise<PartialPersonalAccessToken> => {
        return Promise.resolve({
            id: '4a5f12e2-2bbb-435a-910b-28949f739650',
            partial: 'geti_pat_dNSBPdJ1Y9S',
            name: 'name',
            description: 'description',
            expiresAt: '2024-06-20T11:11:11.062Z',
            organizationId: 'de61b273-a8cf-4dd7-96a4-b5e1c5b131fd',
            userId: 'b82da6f8-5352-4dbb-99d7-84135a811bea',
            createdAt: '2024-02-08T12:17:26Z',
        });
    };

    return { createPersonalAccessToken, getPersonalAccessTokens, deletePersonalAccessToken, updatePersonalAccessToken };
};
